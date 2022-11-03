import mysql.connector
from mysql.connector import ProgrammingError


class MedDRA():

    __pt_to_group = {'soc': {}, 'hlgt': {}, 'hlt': {}, 'pt': {}}
    __pt_to_group_name = {'soc': {}, 'hlgt': {}, 'hlt': {}, 'pt': {}}

    def __init__(self, username, password, host='localhost', database='meddra'):
        self.db = mysql.connector.connect(host=host, database=database, username=username, password=password)

    def getHLGT(self, pt):
        cursor = self.db.cursor()
        cursor.execute(f'SELECT hlgt_code, hlgt_name FROM 1_hlgt_pref_term where hlgt_code in (SELECT hlgt_code FROM meddra.1_md_hierarchy WHERE pt_code = {pt})')
        return {str(pt[0]): pt[1] for pt in cursor.fetchall()}

    def getHLT(self, pt):
        cursor = self.db.cursor()
        cursor.execute(f'SELECT hlt_code, hlt_name FROM 1_hlt_pref_term where hlt_code in (SELECT hlt_code FROM meddra.1_md_hierarchy WHERE pt_code = {pt})')
        return {str(pt[0]): pt[1] for pt in cursor.fetchall()}

    def getSoc(self, pt):
        cursor = self.db.cursor()
        query = f'SELECT soc_code, soc_name FROM 1_soc_term where soc_code in (SELECT soc_code FROM meddra.1_md_hierarchy WHERE pt_code = {pt} and primary_soc_fg = "Y")'
        cursor.execute(query)
        return {str(pt[0]): pt[1] for pt in cursor.fetchall()}

    def getLLT(self, llt):
        cursor = self.db.cursor()
        cursor.execute(f'SELECT pt_code FROM 1_low_level_term where llt_code = {llt}')
        pt = cursor.fetchone()
        return str(pt[0])

    def getPt(self, pt):
        cursor = self.db.cursor()
        cursor.execute(f'SELECT pt_code, pt_name FROM 1_pref_term where pt_code = {pt}')
        result = {}
        for pt in cursor.fetchall():
            result[str(pt[0])] = pt[1]
        if len(result) == 0:
            # try to see if the pt provided is a llt
            pt = self.getLLT(pt)
            if pt is not None:
                return self.getPt(pt)
        return result

    def getHlgtName(self, hlgt_code):
        try:
            cursor = self.db.cursor()
            cursor.execute(f'SELECT hlgt_name FROM 1_hlgt_pref_term where hlgt_code = {hlgt_code}')
            hlgt = cursor.fetchone()
            return hlgt[0]
        except ProgrammingError as e:
            print(f'{e} : {hlgt_code}')

    def getHltName(self, hlt_code):
        try:
            cursor = self.db.cursor()
            cursor.execute(f'SELECT hlt_name FROM 1_hlt_pref_term where hlt_code = {hlt_code}')
            hlt = cursor.fetchone()
            return hlt[0]
        except ProgrammingError as e:
            print(f'{e} : {hlt_code}')

    def getSocName(self, soc_code):
        try:
            cursor = self.db.cursor()
            cursor.execute(f'SELECT soc_name FROM 1_soc_term where soc_code = {soc_code}')
            hlt = cursor.fetchone()
            return hlt[0]
        except ProgrammingError as e:
            print(f'{e} : {soc_code}')

    def getPtName(self, pt_code):
        cursor = self.db.cursor()
        cursor.execute(f'SELECT pt_name FROM 1_pref_term where pt_code = {pt_code}')
        pt = cursor.fetchone()
        return pt[0] if pt is not None else pt_code

    def getBySocName(self, name):
        cursor = self.db.cursor()
        cursor.execute(f'SELECT soc_code FROM 1_soc_term where soc_name like "%{name}%"')
        pts = cursor.fetchall()
        return [pt[0] for pt in pts]

    def map(self, pt, level):
        level2fie = {'pt': self.getPt, 'hlgt': self.getHLGT, 'hlt': self.getHLT, 'soc': self.getSoc}
        if pt not in self.__pt_to_group[level]:
            if level in level2fie:
                group = level2fie[level](pt)
            else:
                return None

            # sometimes the pt is actually a llt. Fix this.
            if len(group) == 0:
                pt = self.getPtForLlt(pt)
                if pt is not None:
                    if level in level2fie:
                        group = level2fie[level](pt)
            self.__pt_to_group[level][pt] = list(group.keys())[0] if len(group) > 0 else None
        return self.__pt_to_group[level][pt]

    def getPtForLlt(self, llt):
        cursor = self.db.cursor()
        cursor.execute(f'SELECT pt_code FROM 1_low_level_term where llt_code = {llt}')
        pts = cursor.fetchall()
        if len(pts) > 0:
            return pts[0][0]
        else:
            return None

    def map2name(self, pt, level):
        if pt not in self.__pt_to_group_name[level]:
            group = self.map(pt, level)
            if group is None:
                print(f'group is None for {pt}')
                name = None
            else:
                if level == 'pt':
                    name = self.getPtName(group)
                elif level == 'hlgt':
                    name = self.getHlgtName(group)
                elif level == 'hlt':
                    name = self.getHltName(group)
                elif level == 'soc':
                    name = self.getSocName(group)
            self.__pt_to_group_name[level][pt] = name

        return self.__pt_to_group_name[level][pt]
