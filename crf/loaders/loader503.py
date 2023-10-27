from . import CRFLoader

class Loader503(CRFLoader):

    def mh_data(self, mh_data):
        
        siCom = self.join_comments('assistance_comment', 'work_comment')
        mh_data['SI']['data']['mh:MedHistData/si_abst[@xsi:type=siData]/siCom'] = siCom

        P_1symp_other = self.find_text_field('P_1symp_other')
        if P_1symp_other != 'NULL':
           P_1symp = '7'
           mh_data['CMH_PAR']['data']['mh:MedHistData/cmhpar_abst[@xsi:type=cmhParData]/P_1symp'] = P_1symp

        
        other_previous_com = self.find_text_field('other_previous_comment')
        other_previous = '1' if other_previous_com != 'NULL' else '0'
        
        mh_data['CMH_PAR']['data']['mh:MedHistData/cmhpar_abst[@xsi:type=cmhParData]/other_previous'] = other_previous

        if mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/marevan_warfarin'] == '1' or mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/DOAK'] == '1':
            mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/anticoagulants'] = '1'

        if mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/insulin'] == '1' or mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/other_antidiabetics'] == '1':
            mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/antidiabetics'] = '1'
        

        st_com = 'NULL'
        
        st_com = self.join_comments('smok_comment', 'stimulants_overuse_comment')
        mh_data['ST']['data']['mh:MedHistData/st_abst[@xsi:type=stData]/st_com'] = st_com
        

        I_1symp_other = self.find_text_field('I_1symp_other')
        if I_1symp_other != 'NULL':
           I_1symp = '7'
           mh_data['CMH_INF']['data']['mh:MedHistData/cmhpar_abst[@xsi:type=cmhInfData]/I_1symp'] = I_1symp

       
        # levodopa_dose = self.year_command('levodopa_dose')
        # mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/levodopa_dose'] = levodopa_dose
        # dbs_year = self.year_command('dbs_year')
        # mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/dbs_year'] = dbs_year

        # duodopa_year = self.year_command('duodopa_year')
        # mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/duodopa_year'] = duodopa_year

        # lecigon_year = self.year_command('lecigon_year')
        # mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/lecigon_year'] = lecigon_year

        # apomorfin_year = self.year_command('apomorfin_year')
        # mh_data['CurMed']['data']['mh:MedHistData/curMed_abst[@xsi:type=curMedData]/apomorfin_year'] = apomorfin_year
        
        if self.data['inf_relation_inf_relation_other'] == '1':
            mh_data['CMH_INF']['data']['mh:MedHistData/cmhinf_abst[@xsi:type=cmhInfData]/inf_relation'] = '4'


        if self.data['iaiAvailable'] != '1':
            mh_data['CMH_INF']['data'][f'mh:MedHistData/cmhinf_abst[@xsi:type=cmhInfData]/I_subcogdec'] = 'NULL'
            mh_data['CMH_INF']['data'][f'mh:MedHistData/cmhinf_abst[@xsi:type=cmhInfData]/I_concern'] = 'NULL'
            mh_data['CMH_INF']['data'][f'mh:MedHistData/cmhinf_abst[@xsi:type=cmhInfData]/I_impair'] = 'NULL'
        # hallucinations multicheck store 0 by default, instad of NA
        # check if the hallucinations checkbox is checked, if it is not, then set to NA
        if self.data['I_hallu'] == 'NA':
            vars = ['I_hallu_auditory',
            'I_hallu_visual',
            'I_hallu_tactile',
            'I_hallu_olfatory',
            'I_hallu_gustatory']
            res = [int(self.data[x]) for x in vars]
            s = sum(res)
            if s == 0:
                for var in vars:
                    mh_data['CMH_INF']['data'][f'mh:MedHistData/cmhinf_abst[@xsi:type=cmhInfData]/{var}'] = 'NULL'
            else:
                mh_data['CMH_INF']['data']['mh:MedHistData/cmhinf_abst[@xsi:type=cmhInfData]/I_hallu'] = '1'

        return mh_data

    # def new_method(self, var):
    #     nums = [self.data[f'{var}_year_{n}'] for n in range(1,5)]
    #     final_number = ''
    #     if not 'NA' in nums:
    #         final_number = ''.join(nums)
    #     return final_number

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