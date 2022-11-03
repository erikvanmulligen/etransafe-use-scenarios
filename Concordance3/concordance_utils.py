def amin(value1, value2):
    if value1 is None:
        if value2 is None:
            return None
        else:
            return value2
    else:
        if value2 is None:
            return value1
        else:
            if value1 >= 0:
                if value2 >= 0:
                    return min(value1, value2)
                else:
                    return value1
            else:
                if value2 >= 0:
                    return value2
                else:
                    return max(value1, value2)


def amax(value1, value2):
    if value1 is None:
        if value2 is None:
            return None
        else:
            return value2
    else:
        if value2 is None:
            return value1
        else:
            if value1 >= 0:
                if value2 >= 0:
                    return max(value1, value2)
                else:
                    return value1
            else:
                if value2 >= 0:
                    return value2
                else:
                    return min(value1, value2)


def identical(groups):
    for i in range(len(groups)):
        if groups[i] != groups[0]:
            return False
    return True


def getKey(finding, clinical):
    result = ''
    if clinical:
        result += finding['clinicalFindingCode']
    else:
        result += finding['preclinicalFindingCode']
        if finding['preclinicalSpecimenOrganCode'] is not None:
            result += '_' + finding['preclinicalSpecimenOrganCode']
    return result


def compute_lrp(grp):
    sensitivity = compute_sensitivity(grp)
    specificity = compute_specificity(grp)
    if specificity is not None and sensitivity is not None:
        return sensitivity / (1 - specificity) if specificity != 1 else None
    else:
        return None


def compute_lrn(grp):
    sensitivity = compute_sensitivity(grp)
    specificity = compute_specificity(grp)
    if specificity is not None and sensitivity is not None:
        return (1 - sensitivity) / specificity if specificity != 0 else None
    else:
        return None


def compute_chisquare(group):
    tp = group['tp']
    fp = group['fp']
    fn = group['fn']
    tn = group['tn']
    total = tp + fp + fn + tn
    e11 = ((tp + fp) * (tp + fn)) / total
    e12 = ((tp + fp) * (fp + tn)) / total
    e21 = ((fn + tn) * (tp + fn)) / total
    e22 = ((fn + tn) * (fp + tn)) / total
    try:
        return (((tp - e11) ** 2) / e11) + (((fp - e12) ** 2) / e12) + (((fn - e21) ** 2) / e21) + (
                    ((tn - e22) ** 2) / e22)
    except ZeroDivisionError as e:
        return None


def compute_sensitivity(group):
    tp = group['tp']
    fn = group['fn']
    return tp / (tp + fn) if (tp + fn) > 0 else None


def compute_specificity(group):
    fp = group['fp']
    tn = group['tn']
    return tn / (fp + tn) if (fp + tn) > 0 else None


def intersect(list1, list2):
    return [x for x in list1 if x in list2]


def getAllClinicalFindings(db):
    cursor = db.cursor()
    cursor.execute('select distinct clinicalFindingCode from mappings')
    result = []
    for r in cursor.fetchall():
        record = {}
        c = 0
        for value in r:
            record[cursor.column_names[c]] = value
            c += 1
        result.append(record)
    return result


def getAllPreclinicalFindings(db):
    cursor = db.cursor()
    cursor.execute('select distinct preclinicalFindingCode, preclinicalSpecimenOrganCode from mappings')
    result = []
    for r in cursor.fetchall():
        record = {}
        c = 0
        for value in r:
            record[cursor.column_names[c]] = value
            c += 1
        result.append(record)
    return result


def getAllDrugPreclinicalFindings(db, inchi):
    cursor = db.cursor()
    sql = f"SELECT findingCode as preclinicalFindingCode, specimenOrganCode as preclinicalSpecimenOrganCode from findings where inchi_key = '{inchi}' and db like 'eToxSys'"
    cursor.execute(sql)
    result = []
    for r in cursor.fetchall():
        record = {}
        c = 0
        for value in r:
            record[cursor.column_names[c]] = value
            c += 1
        result.append(record)
    return result


def convertSQLDict(cursor):
    result = []
    for r in cursor.fetchall():
        record = {}
        c = 0
        for value in r:
            record[cursor.column_names[c]] = value
            c += 1
        result.append(record)
    return result


def getAllDrugClinicalFindings(db, inchi):
    cursor = db.cursor()
    sql = f"SELECT findingCode as clinicalFindingCode from findings where inchi_key = '{inchi}' and db not like 'eToxSys'"
    cursor.execute(sql)
    return convertSQLDict(cursor)


def getMappings(db, max_distance):
    cursor = db.cursor()
    cursor.execute(f'SELECT DISTINCT * FROM mappings WHERE ABS(minDistance) <= {max_distance}')
    return convertSQLDict(cursor)


def getDrugFindings(db, drug, databases, clinical):
    cursor = db.cursor()
    db_str = ','.join(['"{}"'.format(value) for value in databases])
    if clinical:
        sql = f"select clinicalFindingCode from mappings where clinicalFindingCode in (SELECT DISTINCT findingCode from findings where inchi_key = '{drug}' and db in ({db_str}))"
    else:
        sql = f"select clinicalFindingCode from mappings where (preclinicalFindingCode, preclinicalSpecimenOrganCode) in (SELECT findingCode, specimenOrganCode from findings where inchi_key = '{drug}' and db in ({db_str}))"
    cursor.execute(sql)
    return [r[0] for r in cursor.fetchall()]


def getAllPreclinicalClinicalDistances(db, preclinical, clinical):
    cursor = db.cursor()
    pc_db_str = ','.join(['"{}"'.format(value) for value in preclinical])
    cc_db_str = ','.join(['"{}"'.format(value) for value in clinical])
    sql = f'SELECT clinicalFindingCode, minDistance FROM mappings WHERE clinicalFindingCode IN (SELECT DISTINCT findingCode FROM findings WHERE db IN ({cc_db_str})) ' \
          f'UNION ' \
          f'SELECT clinicalFindingCode, minDistance FROM mappings WHERE (preclinicalFindingCode, preclinicalSpecimenOrganCode) IN (SELECT findingCode, specimenOrganCode FROM findings WHERE db IN ({pc_db_str}))'
    cursor.execute(sql)
    return [(r[0], r[1]) for r in cursor.fetchall()]


def getAllDistances(db):
    cursor = db.cursor()
    cursor.execute('select clinicalFindingCode, min(minDistance) from mappings group by clinicalFindingCode')
    return [(r[0], r[1]) for r in cursor.fetchall()]


def getPreclinicalDistances(db, pts, databases):
    cursor = db.cursor()
    db_str = ','.join(['"{}"'.format(value) for value in databases])
    pts_str = ','.join(['"{}"'.format(pt) for pt in pts])
    sql = f'select clinicalFindingCode, minDistance from mappings where clinicalFindingCode in ({pts_str}) and (preclinicalFindingCode, preclinicalSpecimenOrganCode) in (SELECT findingCode, specimenOrganCode from findings where db in ({db_str}))'
    cursor.execute(sql)
    return [(r[0], r[1]) for r in cursor.fetchall()]