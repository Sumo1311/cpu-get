import pandas as pd
from datetime import date
def process_csv(input_file):
    today = date.today().strftime("%Y-%m-%d")  # 重命名变量避免与date模块冲突
    # 读取CSV文件并保留原始数据格式[5](@ref)
    try:
        input_file=fr"data\{today}_output.csv"
        df = pd.read_csv(input_file, dtype=str, keep_default_na=False)
    except Exception as e:
        print(f"文件读取失败：{str(e)}")
        return

    # 格式检测与修正
    total_rows = len(df)
    error_count = 0
    
    # 第一列强制转换为文本类型[9](@ref)
    df.iloc[:, 0] = df.iloc[:, 0].astype(str)
    
    # 处理其他数值列
    for col in df.columns[1:]:
        # 尝试转换为整数，失败则置为0[6,9](@ref)
        converted = pd.to_numeric(df[col], errors='coerce')
        error_count += converted.isna().sum()
        df[col] = converted.fillna(0).astype('int64')

    # 输出结果
    print(f"CSV文件总行数：{total_rows}")
    print(f"格式错误字段数：{error_count}")
    
    # 保存修正后的文件[5](@ref)
    df.to_csv(input_file, index=False)
    return df

# 使用示例
if __name__ == "__main__":
    process_csv('input.csv')