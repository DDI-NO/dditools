
from . import CRFLoader
from pprint import pprint
class Loader460(CRFLoader):
    
    # def __init__(self, data_source, config):
    #    super(Loader460, self).__init__(data_source, config)
        

    def get_subjectdata(self):
        #print(self.get_val('date_day'))
        subj_group = self.get_val('subj_group')
        recruit = self.get_val('subj_group')
        recruit = self.find_checked('recruit', top=5)

        gender = self.get_val('gender')
        if gender == '0':
            gender = 'M'
        elif gender == '1':
            gender = 'F'
        else:
            gender = 'unknown'
        handedness = self.get_val('handedness')
        if handedness == '0':
            handedness = 'right'
        elif handedness == '1':
            handedness = 'left'
        else:
            handedness = 'unknown'
        yob = ''
        if int(self.data['yob_yob_1']) > -1 and int(self.data['yob_yob_2']) > -1:
            yob = f"19{self.data['yob_yob_1']}{self.data['yob_yob_2']}"

        nation = self.find_checked('nation', start=1, top=3)
        if nation != 'NULL':
            if nation == '1':
                nation = '0'
            else:
                nation = '3'
                
        edu_years = self.get_val('edu_years_1')
        edu_level = self.get_val('edu_level')
        

        demographics_data = {
            'xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/gender' : gender,
            'xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/handedness' : handedness,
            'xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/yob' : yob
        }

        dem_data = {
            'dem:ddiDemographicData/subj_group' : self.get_val('subj_group'),
            'dem:ddiDemographicData/recruit' : recruit,
            'dem:ddiDemographicData/nation' : nation,
            'dem:ddiDemographicData/edu_level' : edu_level,
            'dem:ddiDemographicData/edu_years' : edu_years
        }

        return (demographics_data, dem_data)

    def mh_data(self, mh_data):
        #mh_data = super().get_mhdata()        
        # Join assistance_commend and work_comment and assign to this siCom
        # assistance_comment = self.find_text_field('assistance_commend')
        # work_comment = self.find_text_field('work_comment')
        # siCom = ''
        # if assistance_comment != 'NULL':
        #     siCom += assistance_comment
        # if work_comment != 'NULL':
        #     siCom += ('\n' + work_comment) if assistance_comment != 'NULL' else work_comment
        siCom = self.join_comments('assistance_comment', 'work_comment')
        mh_data['SI']['data']['mh:MedHistData/si_abst[@xsi:type=siData]/siCom'] = siCom

        P_1symp_other = self.find_text_field('P_1symp_other')
        if P_1symp_other != 'NULL':
           P_1symp = '7'
           mh_data['CMH_PAR']['data']['mh:MedHistData/cmhpar_abst[@xsi:type=cmhParData]/P_1symp'] = P_1symp

        ## there is a bug in the source tex file, assigning 7 to "Psykotiske symptomer" 
        ## add 1 to the value if >7
        # if mh_data['mh:MedHistData/cmhpar_abst[@xsi:type=cmhParData]/P_1symp'] != 'NULL' and mh_data['mh:MedHistData/cmhpar_abst[@xsi:type=cmhParData]/P_1symp'] != '':
        #     symp = int(mh_data['mh:MedHistData/cmhpar_abst[@xsi:type=cmhParData]/P_1symp'])
        #     if symp >= 7:
        #         symp += 1
        #         mh_data['mh:MedHistData/cmhpar_abst[@xsi:type=cmhParData]/P_1symp'] = str(symp)


        other_previous_com = self.find_text_field('other_previous_comment')
        other_previous = '1' if other_previous_com != 'NULL' else '0'
        
        mh_data['CMH_PAR']['data']['mh:MedHistData/cmhpar_abst[@xsi:type=cmhParData]/other_previous'] = other_previous

        if mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/marevan_warfarin'] == '1' or mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/DOAK'] == '1':
            mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/anticoagulants'] = '1'

        if mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/insulin'] == '1' or mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/other_antidiabetics'] == '1':
            mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/antidiabetics'] = '1'
        
        
        # Alco_unitpweek_1 = mh_data['mh:MedHistData/st_abst[@xsi:type=stData]/Alco_unitpweek_1']
        # Alco_unitpweek_2 = mh_data['mh:MedHistData/st_abst[@xsi:type=stData]/Alco_unitpweek_2']
        # units = ''
        # units = Alco_unitpweek_1 + Alco_unitpweek_2
        # units.replace('NULL', '')
        # mh_data['mh:MedHistData/st_abst[@xsi:type=stData]/units'] = units

        
        # total_str = ''
        # fast1 = mh_data['mh:MedHistData/st_abst[@xsi:type=stData]/fast1']
        # fast2 = mh_data['mh:MedHistData/st_abst[@xsi:type=stData]/fast2']
        # fast3 = mh_data['mh:MedHistData/st_abst[@xsi:type=stData]/fast3']
        # fast4 = mh_data['mh:MedHistData/st_abst[@xsi:type=stData]/fast4']
        # if fast1 != 'NULL' and fast2 != 'NULL' and fast3 != 'NULL' and fast4 != 'NULL':
        #     total_int = int(fast1) + int(fast2) + int(fast3) + int(fast4)
        #     total_str = str(total_int)
        #     mh_data['mh:MedHistData/st_abst[@xsi:type=stData]/fast_tot'] = total_str
        # mh_data['mh:MedHistData/st_abst[@xsi:type=stData]/fast_score_comp'] = '1'

        # join smok_comment and stimulants_overuse_comment to set to 
        # mh:MedHistData/st_abst[@xsi:type=stData]/st_com
        st_com = 'NULL'
        # smok_comment = self.find_text_field('smok_comment')
        st_com = self.join_comments('smok_comment', 'stimulants_overuse_comment')
        mh_data['ST']['data']['mh:MedHistData/st_abst[@xsi:type=stData]/st_com'] = st_com
        
        ## TODO
        ## Add gdeps 30 to XNAT
        I_1symp_other = self.find_text_field('I_1symp_other')
        if I_1symp_other != 'NULL':
           I_1symp = '7'
           mh_data['CMH_INF']['data']['mh:MedHistData/cmhpar_abst[@xsi:type=cmhInfData]/I_1symp'] = I_1symp

        return mh_data

    

    def cs_data(self, cs_data):
        sum_boxes = cs_data['cs']['data']['cs:cogScrData/cdr_abst[@xsi:type=cdrData]/Sum_Boxes']
        cs_data['cs']['data']['cs:cogScrData/cdr_abst[@xsi:type=cdrData]/Sum_Boxes'] = sum_boxes.replace('.0', '')
        return cs_data

    def diag_data(self, diag_data):
        
        val = ''
        scd_symp = self.data['stag_scd_symptoms']
        no_scd_symp = self.data['stag_no_scd_symptoms']
        if scd_symp == '1':
            val = '1'
        if no_scd_symp == '1':
            val = '0'
        
        diag_data['diag']['data']['diag:DiagnosisData/scd_symptoms'] = val

        if self.data['diag_park'] == '43':
            diag_data['diag']['data']['diag:DiagnosisData/diag'] = '43'
        if self.data['diag_park'] == '44':
            diag_data['diag']['data']['diag:DiagnosisData/diag'] = '44'

        diag_data['diag']['data']['diag:DiagnosisData/scd_symptoms'] = val
        return diag_data

    
        
