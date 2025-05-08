import pandas as pd

def process_csv(input_file, output_file):
    # 读取CSV文件，将空字符串和常见占位符识别为空值
    df = pd.read_csv(input_file, na_values=['', 'NA', 'N/A', 'NaN', 'null'])
    
    # 检查第一列是否为文本格式
    first_col = df.columns[0]
    if df[first_col].dtype != 'object':
        print(f"警告: 第一列 '{first_col}' 不是文本格式 (当前类型: {df[first_col].dtype})")
    else:
        print(f"第一列 '{first_col}' 是文本格式")

    # 检测第二列及后续列的空值
    empty_records = []
    for col in df.columns[1:]:
        null_rows = df[df[col].isna()]
        if not null_rows.empty:
            for idx, row in null_rows.iterrows():
                empty_records.append({
                    "行名称": row[first_col],
                    "列名称": col,
                    "行号": idx + 2  # CSV行号从1开始，加上标题行
                })
    
    # 打印空值信息
    if empty_records:
        print("\n发现空值:")
        for record in empty_records:
            print(f"行 '{record['行名称']}' (第{record['行号']}行), 列 '{record['列名称']}'")
    else:
        print("\n所有数据列均无空值")

    # 删除全空列
    empty_columns = df.columns[df.isna().all()].tolist()
    df_cleaned = df.drop(columns=empty_columns)
    
    if empty_columns:
        print(f"\n删除全空列: {', '.join(empty_columns)}")
    else:
        print("\n未发现需要删除的全空列")

    # 保存处理后的文件
    df_cleaned.to_csv(output_file, index=False)
    print(f"\n处理后的文件已保存至: {output_file}")

# 使用示例
process_csv("cpu_sale.csv", "cpu_sale.csv")