import pandas as pd
import numpy as np
import openpyxl
import os

# path: xlsx 파일 들어있는 경로 설정
path = r"C:\Users\leeju\Desktop\raw\tmp"
file_list_all = os.listdir(path)

# 파일명 및 파일 확장자 지정
file_list = []

for file in file_list_all:
    if file.startswith("연립다세대(매매)") & file.endswith(".xlsx"):
        print(file)
        file_list.append(file)

print("***********************************************************")

df = pd.DataFrame()

for file in file_list:
    print(file)
    data = pd.read_excel(path+"\\"+file, header=0, skiprows=16)
    df = pd.concat([df,data])
print("***********************************************************")

# row 수 확인
print('row count = {}'.format(len(df)))

# data 확인
print(df.head(5))

# dataframe column data type 확인
#df.dtypes

# dataframe 대략적인 정보 확인
#df.info()

# 건축년도 nan 데이터 처리(서울특별시 성북구 길음동 1083) -> 0 으로 치환, 데이터 타입 변환 int
#df[df.건축년도.isna()]

df['건축년도'] = df['건축년도'].fillna(0).astype(int)

print(df[(df.번지=='1083')])

# '거래금액(만원)' 쉼표 제거 및 데이터 타입 변환(numeric)
# '거래금액(만원)' 단위 만원 -> 원 으로 변경
#df['거래금액(만원)']
df['거래금액(만원)'] = pd.to_numeric(df['거래금액(만원)'].apply(lambda x: x.replace(',', '')))
df['거래금액(만원)'] = df['거래금액(만원)'] * 10000

# 데이터 분리: 계약년월 -> 계약년도, 계약월
df['계약년월_str'] = df['계약년월'].apply(lambda x: str(x))
df['계약년도'] = df['계약년월_str'].apply(lambda x: x[:4])
df['계약월'] = df['계약년월_str'].apply(lambda x: x[4:])

# 계약일자: datetime 타입의 계약일
df['계약일자'] = df.계약년월*100 + df.계약일
df['계약일자'] = pd.to_datetime(df['계약일자'].apply(lambda x:str(x)))

# 시,구,동 컬럼 생성
df['시'] = df.시군구.str.split(' ').str[0]
df['구'] = df.시군구.str.split(' ').str[1]
df['동'] = df.시군구.str.split(' ').str[2]

# 도로명주소 분리: 도로명, 건물번호
df.rename(columns = {'도로명':'도로명주소'}, inplace=True)
df['도로명'] = df.도로명주소.str.split(' ').str[0]
df['건물번호'] = df.도로명주소.str.split(' ').str[1]

# 컬럼명 재정의
df.columns = ['시군구','번지','본번','부번','건물명','전용면적','대지권면적',
              '계약년월','계약일','거래금액','층',
              '건축년도','도로명주소','해제사유발생일',
              '계약년월_str','계약년도','계약월','계약일자',
             '시','구','동','도로명','건물번호']

# 인플레이션 반영한 거래금액 보정 by using GDP Deflator(기준년도:2015)
file_name = "GDP_Deflator_한국은행.xlsx"
deflator = pd.read_excel(path+"\\"+file_name, header=0)

# 행렬 전환
deflator = deflator.transpose()
deflator = deflator[4:]

# 컬럼명 재정의
deflator.reset_index(drop=False, inplace=True)
deflator.columns = ['년도','물가지수']

# 2021년 물가지수(예상치) append
deflator = deflator.append({'년도':'2021', '물가지수':106.5039}, ignore_index=True)

# 데이터 타입 변환(물가지수: float)
deflator['물가지수'] = deflator['물가지수'].apply(lambda x: float(x))
#deflator.info()

# 물가지수 left join
df = pd.merge(df, deflator, left_on='계약년도', right_on='년도', how='left')

# 거래금액_물가반영
df['거래금액_물가반영'] = df.거래금액*(df.물가지수/100)
df['거래금액_물가반영'] = df['거래금액_물가반영'].astype(np.uint64)

# 거래금액_로그
df['거래금액_로그'] = df['거래금액_물가반영'].apply(lambda x: np.log(x))

# 컬럼 순서 바꾸기
df = df[['시', '구', '동',
         '도로명주소','도로명','건물번호',
         '번지','본번','부번',
         '층','건물명','전용면적','대지권면적','건축년도',
         '계약년월','계약년도','계약월','계약일','계약일자',
         '거래금액','거래금액_물가반영','거래금액_로그',
         '해제사유발생일']]
# df.to_excel('merged_data_v2.xlsx')

print('*********************************************************************start to create excel file')
df.to_excel(path+"\\"+'merged_data_v2.xlsx', index = False)
print('*********************************************************************End of merge_data.py')