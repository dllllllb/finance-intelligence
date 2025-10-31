"""
BNK-25-10-V4.xlsm 파일 상세 분석
"""
import pandas as pd
import openpyxl
import json

def analyze_bnk_file():
    """BNK 엑셀 파일 분석"""
    filepath = "BNK-25-10-V4.xlsm"

    print("=" * 80)
    print("📊 BNK-25-10-V4.xlsm 파일 분석")
    print("=" * 80)
    print()

    # 1. 파일 기본 정보
    print("📁 1. 파일 기본 정보")
    print("-" * 80)
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        sheet_names = wb.sheetnames
        print(f"✓ 시트 개수: {len(sheet_names)}개")
        print(f"✓ 시트 목록:")
        for i, name in enumerate(sheet_names, 1):
            print(f"  {i}. {name}")
        print()
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {e}")
        return

    # 2. 각 시트별 상세 분석
    print("📋 2. 시트별 상세 분석")
    print("-" * 80)

    for sheet_name in sheet_names[:5]:  # 처음 5개 시트만
        print(f"\n🔹 시트: '{sheet_name}'")
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl')

            print(f"  크기: {df.shape[0]}행 × {df.shape[1]}열")

            if df.shape[0] > 0:
                print(f"  컬럼명: {list(df.columns[:10])}" +
                      ("..." if len(df.columns) > 10 else ""))

                # 샘플 데이터 (첫 3행)
                print(f"\n  📝 샘플 데이터 (처음 3행):")
                print(df.head(3).to_string(max_cols=6))

                # 데이터 타입
                print(f"\n  📊 데이터 타입:")
                dtypes_summary = df.dtypes.value_counts()
                for dtype, count in dtypes_summary.items():
                    print(f"    - {dtype}: {count}개 컬럼")

                # 숫자 컬럼 통계
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    print(f"\n  📈 숫자 컬럼 통계 (처음 5개):")
                    stats = df[numeric_cols[:5]].describe()
                    print(stats.to_string())

        except Exception as e:
            print(f"  ❌ 시트 읽기 오류: {e}")

        print()

    if len(sheet_names) > 5:
        print(f"\n⚠️  나머지 {len(sheet_names) - 5}개 시트는 생략됨")

    # 3. 특정 패턴 찾기
    print("\n" + "=" * 80)
    print("🔍 3. 데이터 패턴 분석")
    print("-" * 80)

    # 첫 번째 시트로 패턴 분석
    if len(sheet_names) > 0:
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_names[0], engine='openpyxl')

            # 금액 관련 컬럼 찾기
            amount_cols = [col for col in df.columns if any(keyword in str(col).lower()
                          for keyword in ['금액', '가격', '월', '대여료', 'price', 'amount', 'payment'])]

            if amount_cols:
                print(f"✓ 금액 관련 컬럼 발견: {len(amount_cols)}개")
                for col in amount_cols[:10]:
                    print(f"  - {col}")

            # 계산 가능한 관계 찾기
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 2:
                print(f"\n✓ 숫자 컬럼 간 상관관계 (상위 5개):")
                corr = df[numeric_cols].corr()
                # 대각선 제외하고 높은 상관관계만
                for i in range(min(5, len(numeric_cols))):
                    for j in range(i+1, min(5, len(numeric_cols))):
                        corr_val = corr.iloc[i, j]
                        if abs(corr_val) > 0.5:
                            print(f"  - {numeric_cols[i]} ↔ {numeric_cols[j]}: {corr_val:.3f}")

        except Exception as e:
            print(f"❌ 패턴 분석 오류: {e}")

    print("\n" + "=" * 80)
    print("✅ 분석 완료")
    print("=" * 80)

if __name__ == "__main__":
    analyze_bnk_file()
