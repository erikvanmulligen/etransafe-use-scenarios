import mysql.connector


def getAllPreclinicalFindings(host, database, user, password):
    db = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cursor = db.cursor()
    cursor.execute("SELECT findingCode, specimenOrganCode FROM unique_findings")
    return cursor.fetchall()


def normalizePreclinicalFields(records):
    return [{'organCode': f[1] if f[1] is not None and len(f[1]) > 0 else None, 'code': f[0] if f[0] is not None else ''} for f in records]