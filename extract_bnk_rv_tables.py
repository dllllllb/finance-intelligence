"""
BNK 잔가율 테이블 추출
"""
import pandas as pd
import json

def extract_rv_tables():
    """BNK RVs 시트에서 잔가율 테이블 추출"""
    filepath = "BNK-25-10-V4.xlsm"

    print("="*80)
    print("📊 BNK 잔가율 테이블 추출")
    print("="*80)

    df = pd.read_excel(filepath, sheet_name='RVs', engine='openpyxl', header=None)

    rv_tables = {}

    # 웨스트 통합 (row 3~10)
    print("\n1. 웨스트 통합 2만KM")
    west_unified = {}
    grades = ['S', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    periods = [12, 24, 36, 42, 44, 48, 60]

    for i, period in enumerate(periods):
        row_idx = 4 + i  # 12개월은 row 4
        west_unified[period] = {}
        for j, grade in enumerate(grades):
            col_idx = 1 + j  # S는 col 1
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and value != 0:
                west_unified[period][grade] = float(value)

    rv_tables['웨스트_통합_2만'] = west_unified
    print(f"  추출 완료: {len(west_unified)} 기간")

    # 웨스트 수입 (row 16~23)
    print("\n2. 웨스트 수입 2만KM")
    west_import = {}
    for i, period in enumerate(periods):
        row_idx = 17 + i
        west_import[period] = {}
        for j, grade in enumerate(grades):
            col_idx = 1 + j
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and value != 0:
                west_import[period][grade] = float(value)

    rv_tables['웨스트_수입_2만'] = west_import
    print(f"  추출 완료: {len(west_import)} 기간")

    # 큐브 수입 (row 29~36)
    print("\n3. 큐브 수입 2만KM")
    cube_import = {}
    grades_cube = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']
    for i, period in enumerate(periods):
        row_idx = 30 + i
        cube_import[period] = {}
        for j, grade in enumerate(grades_cube):
            col_idx = 1 + j
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and value != 0:
                cube_import[period][grade] = float(value)

    rv_tables['큐브_수입_2만'] = cube_import
    print(f"  추출 완료: {len(cube_import)} 기간")

    # 무카 국산 (row 40~47)
    print("\n4. 무카 국산 2만KM")
    muca_domestic = {}
    grades_muca = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    for i, period in enumerate(periods):
        row_idx = 41 + i
        muca_domestic[period] = {}
        for j, grade in enumerate(grades_muca[:16]):  # Q까지만
            col_idx = 1 + j
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and value != 0:
                muca_domestic[period][grade] = float(value)

    rv_tables['무카_국산_2만'] = muca_domestic
    print(f"  추출 완료: {len(muca_domestic)} 기간")

    # 개월수별 감가율 테이블 (col 31~61)
    print("\n5. 개월수별 감가율 테이블")
    depreciation_table = {}
    for month in range(1, 61):  # 1~60개월
        row_idx = 6 + month  # 1개월은 row 7
        col_idx = 32  # 감가율은 col 32
        value = df.iloc[row_idx, col_idx]
        if pd.notna(value):
            depreciation_table[month] = float(value)

    rv_tables['감가율_테이블'] = depreciation_table
    print(f"  추출 완료: {len(depreciation_table)} 개월")

    # 주행거리 조정
    rv_tables['주행거리_조정'] = {
        '1만': +0.02,   # +2%p
        '1.5만': +0.01, # +1%p
        '2만': 0,       # 기준
        '3만': -0.03    # -3%p
    }

    # JSON으로 저장
    output_path = "src/bnk_rv_tables.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rv_tables, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {output_path}")
    print(f"총 {len(rv_tables)} 테이블 추출")

    # 샘플 출력
    print("\n📋 샘플 데이터:")
    print(f"웨스트 통합 36개월 S등급: {rv_tables['웨스트_통합_2만'][36]['S']}")
    print(f"감가율 12개월: {rv_tables['감가율_테이블'][12]}")

    print("\n" + "="*80)

if __name__ == "__main__":
    extract_rv_tables()
