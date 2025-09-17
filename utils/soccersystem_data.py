# utils/soccersystem_data.py
import pandas as pd
from sqlalchemy import create_engine, inspect
from typing import List, Optional

from config import SOCCER_DATABASE_URL, SOCCER_DB_NAME, DB_HOST, SOCCER_DB_HOST, SOCCER_DB_PORT, SOCCER_DB_USER


def get_soccersystem_engine():
    """
    Crea un engine SQLAlchemy hacia la BD secundaria 'soccersystem'.
    """
    try:
        if not SOCCER_DATABASE_URL:
            return None
        engine = create_engine(SOCCER_DATABASE_URL)
        # Test rápido
        _ = engine.connect()
        _.close()
        return engine
    except Exception as e:
        print(f"[ANTROPO][ERROR] No se pudo conectar a soccersystem: {e}")
        return None


def _find_first_column(cols: List[str], candidates: List[str]) -> Optional[str]:
    """
    Devuelve el primer nombre de columna que exista en 'cols' entre los 'candidates'.
    """
    for c in candidates:
        if c in cols:
            return c
    return None


def get_team_players(team_id: int = 95) -> pd.DataFrame:
    """
    Obtiene jugadores del equipo dado desde las tablas 'player_team' y 'players'.
    Devuelve columnas: player_id, full_name y (si existe) dni.
    """
    engine = get_soccersystem_engine()
    if engine is None:
        print("[ANTROPO] Engine soccersystem es None")
        return pd.DataFrame(columns=["player_id", "full_name", "dni"])  # vacío seguro

    insp = inspect(engine)
    tables = set(insp.get_table_names())
    if not {"player_team", "players"}.issubset(tables):
        print(f"[ANTROPO] Tablas requeridas faltantes. Disponibles: {tables}")
        return pd.DataFrame(columns=["player_id", "full_name", "dni"])  # tablas faltantes

    # 1) player_team -> obtener player_ids del equipo
    try:
        pt_table_cols = [c['name'] for c in insp.get_columns('player_team')]
        team_col = _find_first_column(pt_table_cols, ["team_id", "id_team", "team", "equipo_id", "club_id"])  # heurística equipo
        player_id_col = _find_first_column(pt_table_cols, ["player_id", "player", "id_player", "athlete_id"])  # heurística jugador
        if not player_id_col:
            print("[ANTROPO] player_team sin columna de jugador reconocible")
            return pd.DataFrame(columns=["player_id", "full_name", "dni"])  # sin columna jugador

        if team_col:
            query = f"SELECT {player_id_col} AS player_id FROM player_team WHERE {team_col} = %s"
            pt_df = pd.read_sql(query, engine, params=(team_id,))
        else:
            # No podemos filtrar por equipo si no encontramos la columna de equipo
            print("[ANTROPO] player_team sin columna de equipo reconocible")
            return pd.DataFrame(columns=["player_id", "full_name", "dni"])  # tablas sin columna de equipo
    except Exception as e:
        print(f"[ANTROPO][ERROR] Consulta player_team falló: {e}")
        return pd.DataFrame(columns=["player_id", "full_name", "dni"])  # fallo consulta

    if pt_df.empty:
        print(f"[ANTROPO] Sin jugadores para team_id={team_id} en player_team")
        return pd.DataFrame(columns=["player_id", "full_name", "dni"])  # sin jugadores

    # Normalizar nombre de columna
    if "player_id" in pt_df.columns:
        player_ids = pt_df["player_id"].dropna().unique().tolist()
    else:
        # Fallback improbable si alias falló
        player_ids = pt_df.iloc[:, 0].dropna().unique().tolist()
    if not player_ids:
        print("[ANTROPO] Lista player_ids vacía tras filtrar player_team")
        return pd.DataFrame(columns=["player_id", "full_name", "dni"])  # vacío

    # 2) players -> info de nombre y dni
    try:
        pl_table_cols = [c['name'] for c in insp.get_columns('players')]
        id_key = _find_first_column(pl_table_cols, ["id", "player_id", "id_player"]) or "id"
        placeholders = ",".join(["%s"] * len(player_ids))
        query = f"SELECT * FROM players WHERE {id_key} IN ({placeholders})"
        players_df = pd.read_sql(query, engine, params=tuple(player_ids))
    except Exception:
        return pd.DataFrame(columns=["player_id", "full_name", "dni"])  # fallo consulta

    if players_df.empty:
        print("[ANTROPO] Tabla players no devolvió filas para los ids indicados")
        return pd.DataFrame(columns=["player_id", "player_name", "dni"])  # sin filas

    pl_cols = list(players_df.columns)
    id_col = _find_first_column(pl_cols, ["id", "player_id", "id_player"]) or "id"
    # Posibles columnas de nombre
    fn_col = _find_first_column(pl_cols, ["first_name", "nombre", "given_name"])  # nombre
    ln_col = _find_first_column(pl_cols, ["last_name", "apellidos", "family_name"])  # apellidos
    name_col = _find_first_column(pl_cols, ["name", "full_name"])  # nombre completo
    nick_col = _find_first_column(pl_cols, ["nick", "nickname", "alias", "short_name"])  # nick
    dni_col = _find_first_column(pl_cols, ["dni", "document", "nif", "doc", "documento"])  # documento

    out = pd.DataFrame()
    out["player_id"] = players_df[id_col]

    # Priorizar nick sobre full_name
    if nick_col:
        out["player_name"] = players_df[nick_col].astype(str)
    elif fn_col and ln_col:
        out["player_name"] = players_df[fn_col].fillna("").astype(str).str.strip() + " " + players_df[ln_col].fillna("").astype(str).str.strip()
    elif name_col:
        out["player_name"] = players_df[name_col].astype(str)
    else:
        # fallback al id como string
        out["player_name"] = players_df[id_col].astype(str)

    # Mantener full_name para compatibilidad si es necesario
    if fn_col and ln_col:
        out["full_name"] = players_df[fn_col].fillna("").astype(str).str.strip() + " " + players_df[ln_col].fillna("").astype(str).str.strip()
    elif name_col:
        out["full_name"] = players_df[name_col].astype(str)
    else:
        out["full_name"] = out["player_name"]

    if dni_col:
        out["dni"] = players_df[dni_col].astype(str)
    else:
        out["dni"] = None

    return out

def get_team_anthropometry_timeseries(category: str = "Primer Equipo") -> pd.DataFrame:
    """
    Devuelve una serie temporal por jugador filtrando directamente por categoría en la tabla antropometria_pedrosa.
    Columnas devueltas:
      - player_name (usando 'hoja' de la tabla)
      - fecha
      - kg_a_bajar, pct_grasa, sum_pliegues, peso
    """
    engine = get_soccersystem_engine()
    if engine is None:
        return pd.DataFrame(columns=[
            "player_name", "fecha", "kg_a_bajar", "pct_grasa", "sum_pliegues", "peso"
        ])

    insp = inspect(engine)
    if "antropometria_pedrosa" not in set(insp.get_table_names()):
        return pd.DataFrame(columns=[
            "player_name", "fecha", "kg_a_bajar", "pct_grasa", "sum_pliegues", "peso"
        ])

    try:
        # Filtrar directamente por categoría en la tabla antropometrica
        query = "SELECT * FROM antropometria_pedrosa WHERE categoria = %s"
        df = pd.read_sql(query, engine, params=(category,))
    except Exception as e:
        print(f"[ANTROPO][ERROR] Error al consultar antropometria_pedrosa por categoría: {e}")
        return pd.DataFrame(columns=[
            "player_name", "fecha", "kg_a_bajar", "pct_grasa", "sum_pliegues", "peso"
        ])

    if df.empty:
        return pd.DataFrame(columns=[
            "player_name", "fecha", "kg_a_bajar", "pct_grasa", "sum_pliegues", "peso"
        ])

    # Procesar los datos igual que antes pero sin necesidad de mapping
    cols = list(df.columns)
    hoja_col = _find_first_column(cols, ["hoja", "nombre_pedrosa"]) or "hoja"
    kg_col = _find_first_column(cols, ["kg_a_bajar", "kg_bajar", "kg_pendientes"])
    pct_col = _find_first_column(cols, ["porcentaje_grasa", "pct_grasa", "%grasa", "porc_grasa", "grasa_pct", "grasa_porcentaje"])
    sumpli_col = _find_first_column(cols, ["sum_pliegues", "suma_pliegues", "pliegues_suma", "suma_pli", "sum_pli", "sumapliegues"])
    peso_col = _find_first_column(cols, ["peso_kg", "peso", "peso_actual", "weight"])
    fecha_col = _find_first_column(cols, ["fecha", "fecha_medicion", "date", "created_at"])
    
    # Columnas para cálculo de % grasa (4 pliegues)
    tricipital_col = _find_first_column(cols, ["tricipital_media", "tricipital", "triceps_media", "triceps"])
    subescapular_col = _find_first_column(cols, ["subescapular_media", "subescapular", "subesacapular_media"])
    suprailiaco_col = _find_first_column(cols, ["suprailiaco_media", "suprailiaco", "supra_iliaco_media"])
    abdominal_col = _find_first_column(cols, ["abdominal_media", "abdominal", "abd_media"])
    
    # Columnas adicionales para suma de pliegues (6 pliegues total)
    muslo_anterior_col = _find_first_column(cols, ["muslo_anterior_media", "muslo_anterior", "muslo_ant_media"])
    pierna_medial_col = _find_first_column(cols, ["pierna_medial_media", "pierna_medial", "pierna_med_media"])

    out = pd.DataFrame()
    out["player_name"] = df[hoja_col].astype(str).str.strip().str.upper()
    out["kg_a_bajar"] = pd.to_numeric(df.get(kg_col), errors="coerce") if kg_col else None
    
    # Calcular % grasa usando la fórmula específica
    if tricipital_col and subescapular_col and suprailiaco_col and abdominal_col:
        tricipital = pd.to_numeric(df.get(tricipital_col), errors="coerce")
        subescapular = pd.to_numeric(df.get(subescapular_col), errors="coerce")
        suprailiaco = pd.to_numeric(df.get(suprailiaco_col), errors="coerce")
        abdominal = pd.to_numeric(df.get(abdominal_col), errors="coerce")
        
        # Fórmula: SUMA(tricipital + subescapular + suprailiaco + abdominal) * 0.153 + 5.783
        suma_pliegues_4 = tricipital + subescapular + suprailiaco + abdominal
        out["pct_grasa"] = suma_pliegues_4 * 0.153 + 5.783
        
        # Calcular suma de 6 pliegues (los 4 anteriores + muslo anterior + pierna medial)
        suma_pliegues_6 = suma_pliegues_4
        if muslo_anterior_col:
            muslo_anterior = pd.to_numeric(df.get(muslo_anterior_col), errors="coerce")
            suma_pliegues_6 = suma_pliegues_6 + muslo_anterior
        if pierna_medial_col:
            pierna_medial = pd.to_numeric(df.get(pierna_medial_col), errors="coerce")
            suma_pliegues_6 = suma_pliegues_6 + pierna_medial
        
        # Usar suma de 6 pliegues si no existe la columna
        if not sumpli_col:
            out["sum_pliegues"] = suma_pliegues_6
    else:
        # Fallback a columna existente si no se pueden calcular
        out["pct_grasa"] = pd.to_numeric(df.get(pct_col), errors="coerce") if pct_col else None
    
    if sumpli_col and "sum_pliegues" not in out.columns:
        out["sum_pliegues"] = pd.to_numeric(df.get(sumpli_col), errors="coerce")
    
    out["peso"] = pd.to_numeric(df.get(peso_col), errors="coerce") if peso_col else None
    if fecha_col and fecha_col in df.columns:
        out["fecha"] = pd.to_datetime(df[fecha_col], errors="coerce")
    else:
        out["fecha"] = pd.NaT
    
    return out

# backward alias (typo compatibility)
get_team_antropometry_timeseries = get_team_anthropometry_timeseries


def get_player_team_for_team(team_id: int = 95) -> pd.DataFrame:
    """
    Devuelve las filas crudas de 'player_team' para un team_id dado.
    Normaliza las columnas a: player_id, team_id si existen.
    """
    engine = get_soccersystem_engine()
    if engine is None:
        print("[ANTROPO] Engine soccersystem es None (player_team raw)")
        return pd.DataFrame(columns=["player_id", "team_id"])  # vacío

    insp = inspect(engine)
    if "player_team" not in set(insp.get_table_names()):
        print("[ANTROPO] Falta tabla player_team (player_team raw)")
        return pd.DataFrame(columns=["player_id", "team_id"])  # falta tabla

    try:
        pt_cols = [c['name'] for c in insp.get_columns('player_team')]
        team_col = _find_first_column(pt_cols, ["team_id", "id_team", "team", "equipo_id", "club_id"])  # heurística equipo
        pid_col = _find_first_column(pt_cols, ["player_id", "player", "id_player", "athlete_id"])  # heurística jugador
        if not pid_col:
            print("[ANTROPO] player_team sin col de jugador (player_team raw)")
            return pd.DataFrame(columns=["player_id", "team_id"])  # sin columna jugador

        if team_col:
            query = f"SELECT {pid_col} AS player_id, {team_col} AS team_id FROM player_team WHERE {team_col} = %s"
            df = pd.read_sql(query, engine, params=(team_id,))
        else:
            # Sin columna de equipo, devolver todo con alias de player_id
            query = f"SELECT {pid_col} AS player_id FROM player_team"
            df = pd.read_sql(query, engine)
            df["team_id"] = None
        print(f"[ANTROPO] player_team raw filas para team_id={team_id}: {len(df)}")
        return df
    except Exception as e:
        print(f"[ANTROPO][ERROR] player_team raw falló: {e}")
        return pd.DataFrame(columns=["player_id", "team_id"])  # fallo consulta


def get_soccer_diagnostics(team_id: int = 95) -> dict:
    """
    Devuelve información de diagnóstico sobre la conexión y el esquema:
    - db_host, db_name, conectado
    - tablas disponibles
    - columnas y recuentos básicos de player_team y players
    """
    diag: dict = {
        "db_host": DB_HOST,
        "db_name": SOCCER_DB_NAME,
        "connected": False,
        "soccer_host": SOCCER_DB_HOST,
        "soccer_port": SOCCER_DB_PORT,
        "soccer_user": SOCCER_DB_USER,
    }
    engine = get_soccersystem_engine()
    if engine is None:
        return diag

    diag["connected"] = True
    insp = inspect(engine)
    try:
        tables = insp.get_table_names()
    except Exception as e:
        diag["tables_error"] = str(e)
        return diag
    diag["tables"] = tables

    # player_team
    if "player_team" in tables:
        try:
            pt_cols = [c['name'] for c in insp.get_columns('player_team')]
        except Exception as e:
            diag["player_team"] = {"columns_error": str(e)}
        else:
            team_col = _find_first_column(pt_cols, ["team_id", "id_team", "team", "equipo_id", "club_id"])  # heurística equipo
            pid_col = _find_first_column(pt_cols, ["player_id", "player", "id_player", "athlete_id"])  # heurística jugador
            info = {"columns": pt_cols, "team_col": team_col, "player_col": pid_col}
            # counts
            try:
                cnt_total = pd.read_sql("SELECT COUNT(*) AS c FROM player_team", engine)
                # usar iloc para evitar errores de iat callable
                info["count_total"] = int(cnt_total.iloc[0, 0])
            except Exception as e:
                info["count_total_error"] = str(e)
            if team_col:
                try:
                    cnt_team = pd.read_sql(
                        f"SELECT COUNT(*) AS c FROM player_team WHERE {team_col} = %s",
                        engine,
                        params=(team_id,),
                    )
                    info["count_team"] = int(cnt_team.iloc[0, 0])
                except Exception as e:
                    info["count_team_error"] = str(e)
            diag["player_team"] = info

    # players
    if "players" in tables:
        try:
            pl_cols = [c['name'] for c in insp.get_columns('players')]
        except Exception as e:
            diag["players"] = {"columns_error": str(e)}
        else:
            id_key = _find_first_column(pl_cols, ["id", "player_id", "id_player"]) or "id"
            info = {"columns": pl_cols, "id_key": id_key}
            try:
                cnt_total = pd.read_sql("SELECT COUNT(*) AS c FROM players", engine)
                info["count_total"] = int(cnt_total.iloc[0, 0])
            except Exception as e:
                info["count_total_error"] = str(e)
            diag["players"] = info

    return diag


def get_player_pedrosa_mapping() -> pd.DataFrame:
    """
    Devuelve un DataFrame con el mapeo a 'nombre_pedrosa' desde la tabla 'mapeo_nombre_dni'.
    Intenta mapear por player_id si existe; si no, por dni.
    Columnas devueltas posibles: ['player_id', 'nombre_pedrosa'] o ['dni', 'nombre_pedrosa']
    """
    engine = get_soccersystem_engine()
    if engine is None:
        print("[ANTROPO] Engine soccersystem es None (mapping)")
        return pd.DataFrame(columns=["player_id", "dni", "nombre_pedrosa"])  # vacío

    insp = inspect(engine)
    if "mapeo_nombre_dni" not in set(insp.get_table_names()):
        print("[ANTROPO] Falta tabla mapeo_nombre_dni")
        return pd.DataFrame(columns=["player_id", "dni", "nombre_pedrosa"])  # falta tabla

    try:
        map_df = pd.read_sql("SELECT * FROM mapeo_nombre_dni", engine)
    except Exception as e:
        print(f"[ANTROPO][ERROR] Consulta mapeo_nombre_dni falló: {e}")
        return pd.DataFrame(columns=["player_id", "dni", "nombre_pedrosa"])  # fallo consulta

    if map_df.empty:
        print("[ANTROPO] mapeo_nombre_dni está vacío")
        return pd.DataFrame(columns=["player_id", "dni", "nombre_pedrosa"])  # vacío

    cols = list(map_df.columns)
    pedrosa_col = _find_first_column(cols, ["nombre_pedrosa", "pedrosa_nombre", "hoja"]) or "nombre_pedrosa"
    pid_col = _find_first_column(cols, ["player_id", "id_player", "player"])  # id jugador
    dni_col = _find_first_column(cols, ["dni", "document", "nif", "doc", "documento"])  # documento

    out_cols = {}
    if pid_col:
        out_cols["player_id"] = map_df[pid_col]
    if dni_col:
        out_cols["dni"] = map_df[dni_col].astype(str)
    out_cols["nombre_pedrosa"] = map_df[pedrosa_col].astype(str)

    out = pd.DataFrame(out_cols)
    # Normalizar espacios/blancos
    out["nombre_pedrosa"] = out["nombre_pedrosa"].str.strip()
    if "dni" in out.columns:
        out["dni"] = out["dni"].str.strip()
    return out


def get_antropometria_for_hojas(hojas: List[str]) -> pd.DataFrame:
    """
    Devuelve última fila por 'hoja' desde 'antropometria_pedrosa' para las hojas dadas.
    Retorna columnas: hoja, kg_a_bajar (si existe), y (si existe) fecha/id usados para ordenar.
    """
    if not hojas:
        print("[ANTROPO] Lista de hojas vacía (sin mapeo a nombre_pedrosa)")
        return pd.DataFrame(columns=["hoja", "kg_a_bajar"])

    engine = get_soccersystem_engine()
    if engine is None:
        print("[ANTROPO] Engine soccersystem es None (antropometría)")
        return pd.DataFrame(columns=["hoja", "kg_a_bajar"])

    insp = inspect(engine)
    if "antropometria_pedrosa" not in set(insp.get_table_names()):
        print("[ANTROPO] Falta tabla antropometria_pedrosa")
        return pd.DataFrame(columns=["hoja", "kg_a_bajar"])

    try:
        placeholders = ",".join(["%s"] * len(hojas))
        query = f"SELECT * FROM antropometria_pedrosa WHERE hoja IN ({placeholders})"
        df = pd.read_sql(query, engine, params=tuple(hojas))
    except Exception as e:
        print(f"[ANTROPO][ERROR] Consulta antropometria_pedrosa falló: {e}")
        return pd.DataFrame(columns=["hoja", "kg_a_bajar"])  # fallo consulta

    if df.empty:
        print("[ANTROPO] antropometria_pedrosa no devolvió filas para las hojas indicadas")
        return pd.DataFrame(columns=["hoja", "kg_a_bajar"])  # sin datos

    cols = list(df.columns)
    hoja_col = _find_first_column(cols, ["hoja", "nombre_pedrosa"]) or "hoja"
    kg_col = _find_first_column(cols, ["kg_a_bajar", "kg_bajar", "kg_pendientes"])  # heurística
    # métricas adicionales
    pct_col = _find_first_column(cols, ["porcentaje_grasa", "pct_grasa", "%grasa", "porc_grasa", "grasa_pct", "grasa_porcentaje"])  # % grasa
    sumpli_col = _find_first_column(cols, ["sum_pliegues", "suma_pliegues", "pliegues_suma", "suma_pli", "sum_pli", "sumapliegues"])  # pliegues
    peso_col = _find_first_column(cols, ["peso_kg", "peso", "peso_actual", "weight"])  # peso
    pesoideal_col = _find_first_column(cols, ["peso_ideal", "peso_id", "weight_ideal", "ideal_weight"])  # peso ideal
    fecha_col = _find_first_column(cols, ["fecha", "fecha_medicion", "date", "created_at"])  # fecha
    id_col = _find_first_column(cols, ["id", "pk"])  # id para ordenar si no hay fecha

    # Seleccionar última fila por hoja
    if fecha_col and fecha_col in df.columns:
        df_sorted = df.sort_values(by=[hoja_col, fecha_col])
        last_df = df_sorted.groupby(hoja_col, as_index=False).tail(1)
    elif id_col and id_col in df.columns:
        df_sorted = df.sort_values(by=[hoja_col, id_col])
        last_df = df_sorted.groupby(hoja_col, as_index=False).tail(1)
    else:
        # Sin orden claro: tomar la primera por hoja
        last_df = df.drop_duplicates(subset=[hoja_col], keep="last")

    out = pd.DataFrame()
    out["hoja"] = last_df[hoja_col].astype(str).str.strip()
    # valores numéricos normalizados
    out["kg_a_bajar"] = pd.to_numeric(last_df.get(kg_col), errors="coerce") if kg_col else None
    out["pct_grasa"] = pd.to_numeric(last_df.get(pct_col), errors="coerce") if pct_col else None
    out["sum_pliegues"] = pd.to_numeric(last_df.get(sumpli_col), errors="coerce") if sumpli_col else None
    out["peso"] = pd.to_numeric(last_df.get(peso_col), errors="coerce") if peso_col else None
    out["peso_ideal"] = pd.to_numeric(last_df.get(pesoideal_col), errors="coerce") if pesoideal_col else None
    if fecha_col and fecha_col in last_df.columns:
        out["fecha"] = pd.to_datetime(last_df[fecha_col], errors="coerce")
    return out


def get_antropometria_timeseries_for_hojas(hojas: List[str]) -> pd.DataFrame:
    """
    Devuelve TODAS las filas por 'hoja' desde 'antropometria_pedrosa' para las hojas dadas.
    Columnas normalizadas devueltas (si existen):
      - hoja (str)
      - fecha (datetime)
      - kg_a_bajar (float)
      - pct_grasa (float)
      - sum_pliegues (float)
      - peso (float)
      - id (para orden secundario)
    """
    if not hojas:
        return pd.DataFrame(columns=["hoja", "fecha", "kg_a_bajar", "pct_grasa", "sum_pliegues", "peso", "id"]) 

    engine = get_soccersystem_engine()
    if engine is None:
        return pd.DataFrame(columns=["hoja", "fecha", "kg_a_bajar", "pct_grasa", "sum_pliegues", "peso", "id"]) 

    insp = inspect(engine)
    if "antropometria_pedrosa" not in set(insp.get_table_names()):
        return pd.DataFrame(columns=["hoja", "fecha", "kg_a_bajar", "pct_grasa", "sum_pliegues", "peso", "id"]) 

    try:
        placeholders = ",".join(["%s"] * len(hojas))
        query = f"SELECT * FROM antropometria_pedrosa WHERE hoja IN ({placeholders})"
        df = pd.read_sql(query, engine, params=tuple(hojas))
    except Exception:
        return pd.DataFrame(columns=["hoja", "fecha", "kg_a_bajar", "pct_grasa", "sum_pliegues", "peso", "id"]) 

    if df.empty:
        return pd.DataFrame(columns=["hoja", "fecha", "kg_a_bajar", "pct_grasa", "sum_pliegues", "peso", "id"]) 

    cols = list(df.columns)
    hoja_col = _find_first_column(cols, ["hoja", "nombre_pedrosa"]) or "hoja"
    kg_col = _find_first_column(cols, ["kg_a_bajar", "kg_bajar", "kg_pendientes"])  # heurística
    pct_col = _find_first_column(cols, ["porcentaje_grasa", "pct_grasa", "%grasa", "porc_grasa", "grasa_pct", "grasa_porcentaje"])  # % grasa
    sumpli_col = _find_first_column(cols, ["sum_pliegues", "suma_pliegues", "pliegues_suma", "suma_pli", "sum_pli", "sumapliegues"])  # pliegues
    peso_col = _find_first_column(cols, ["peso_kg", "peso", "peso_actual", "weight"])  # peso
    fecha_col = _find_first_column(cols, ["fecha", "fecha_medicion", "date", "created_at"])  # fecha
    id_col = _find_first_column(cols, ["id", "pk"])  # id para orden secundario
    
    # Columnas para cálculo de % grasa (4 pliegues)
    tricipital_col = _find_first_column(cols, ["tricipital_media", "tricipital", "triceps_media", "triceps"])
    subescapular_col = _find_first_column(cols, ["subescapular_media", "subescapular", "subesacapular_media"])
    suprailiaco_col = _find_first_column(cols, ["suprailiaco_media", "suprailiaco", "supra_iliaco_media"])
    abdominal_col = _find_first_column(cols, ["abdominal_media", "abdominal", "abd_media"])
    
    # Columnas adicionales para suma de pliegues (6 pliegues total)
    muslo_anterior_col = _find_first_column(cols, ["muslo_anterior_media", "muslo_anterior", "muslo_ant_media"])
    pierna_medial_col = _find_first_column(cols, ["pierna_medial_media", "pierna_medial", "pierna_med_media"])

    out = pd.DataFrame()
    out["hoja"] = df[hoja_col].astype(str).str.strip()
    out["kg_a_bajar"] = pd.to_numeric(df.get(kg_col), errors="coerce") if kg_col else None
    
    # Calcular % grasa usando la fórmula específica
    if tricipital_col and subescapular_col and suprailiaco_col and abdominal_col:
        tricipital = pd.to_numeric(df.get(tricipital_col), errors="coerce")
        subescapular = pd.to_numeric(df.get(subescapular_col), errors="coerce")
        suprailiaco = pd.to_numeric(df.get(suprailiaco_col), errors="coerce")
        abdominal = pd.to_numeric(df.get(abdominal_col), errors="coerce")
        
        # Fórmula: SUMA(tricipital + subescapular + suprailiaco + abdominal) * 0.153 + 5.783
        suma_pliegues_4 = tricipital + subescapular + suprailiaco + abdominal
        out["pct_grasa"] = suma_pliegues_4 * 0.153 + 5.783
        
        # Calcular suma de 6 pliegues (los 4 anteriores + muslo anterior + pierna medial)
        suma_pliegues_6 = suma_pliegues_4
        if muslo_anterior_col:
            muslo_anterior = pd.to_numeric(df.get(muslo_anterior_col), errors="coerce")
            suma_pliegues_6 = suma_pliegues_6 + muslo_anterior
        if pierna_medial_col:
            pierna_medial = pd.to_numeric(df.get(pierna_medial_col), errors="coerce")
            suma_pliegues_6 = suma_pliegues_6 + pierna_medial
        
        # Usar suma de 6 pliegues si no existe la columna
        if not sumpli_col:
            out["sum_pliegues"] = suma_pliegues_6
    else:
        # Fallback a columna existente si no se pueden calcular
        out["pct_grasa"] = pd.to_numeric(df.get(pct_col), errors="coerce") if pct_col else None
    
    if sumpli_col and "sum_pliegues" not in out.columns:
        out["sum_pliegues"] = pd.to_numeric(df.get(sumpli_col), errors="coerce")
    
    out["peso"] = pd.to_numeric(df.get(peso_col), errors="coerce") if peso_col else None
    if fecha_col and fecha_col in df.columns:
        out["fecha"] = pd.to_datetime(df[fecha_col], errors="coerce")
    else:
        out["fecha"] = pd.NaT
    out["id"] = pd.to_numeric(df.get(id_col), errors="coerce") if id_col else None
    return out


def get_team_anthropometry(team_id: int = 95) -> pd.DataFrame:
    """
    Devuelve un DataFrame con columnas:
      - player_id
      - player_name
      - pedrosa_hoja
      - kg_a_bajar
    """
    players = get_team_players(team_id)
    if players.empty:
        print(f"[ANTROPO] get_team_players vacío para team_id={team_id}")
        return pd.DataFrame(columns=["player_id", "player_name", "pedrosa_hoja", "kg_a_bajar"])

    mapping = get_player_pedrosa_mapping()
    pedrosa_col = "nombre_pedrosa" if "nombre_pedrosa" in mapping.columns else None

    merged = None
    if "player_id" in mapping.columns:
        merged = players.merge(mapping[[c for c in ["player_id", "nombre_pedrosa", "dni"] if c in mapping.columns]], on="player_id", how="left")
    elif "dni" in mapping.columns and "dni" in players.columns:
        # asegurar tipo string para ambas
        players_loc = players.copy()
        players_loc["dni"] = players_loc["dni"].astype(str).str.strip()
        mapping_loc = mapping.copy()
        mapping_loc["dni"] = mapping_loc["dni"].astype(str).str.strip()
        merged = players_loc.merge(mapping_loc[[c for c in ["dni", "nombre_pedrosa"] if c in mapping_loc.columns]], on="dni", how="left")
    else:
        # no hay forma de mapear
        print("[ANTROPO] No hay columnas para mapear (player_id/dni)")
        merged = players.copy()
        merged["nombre_pedrosa"] = None

    # Antropometría
    hojas = merged["nombre_pedrosa"].dropna().astype(str).str.strip().unique().tolist()
    print(f"[ANTROPO] Jugadores equipo: {len(players)} | Con mapeo: {merged['nombre_pedrosa'].notna().sum()} | Hojas únicas: {len(hojas)}")
    antropo = get_antropometria_for_hojas(hojas)
    print(f"[ANTROPO] Filas antropometría recuperadas: {len(antropo)}")

    result = merged.merge(antropo, left_on="nombre_pedrosa", right_on="hoja", how="left")

    out = pd.DataFrame()
    out["player_id"] = result["player_id"]
    out["player_name"] = result["full_name"]
    out["pedrosa_hoja"] = result.get("nombre_pedrosa")
    out["kg_a_bajar"] = result.get("kg_a_bajar")

    return out
