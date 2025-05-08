import csv
from datetime import date 
def append_column(input_file, output_file):
    # 读取输入文件的第二列
    new_column = []
    with open(input_file, 'r', newline='') as f_in:
        reader = csv.reader(f_in)
        for row in reader:
            new_column.append(row[1] if len(row) >= 2 else '')
    
    # 读取目标文件现有数据
    existing_data = []
    try:
        with open(output_file, 'r', newline='') as f_out:
            reader = csv.reader(f_out)
            existing_data = list(reader)
    except FileNotFoundError:
        pass
    
    # 计算最大行数以兼容不同行数
    max_rows = max(len(existing_data), len(new_column))
    
    # 合并数据
    merged_data = []
    for i in range(max_rows):
        # 获取现有行或创建新行
        row = existing_data[i].copy() if i < len(existing_data) else []
        # 追加新列值或空字符串
        row.append(new_column[i] if i < len(new_column) else '')
        merged_data.append(row)
    
    # 写入目标文件
    with open(output_file, 'w', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerows(merged_data)

# 使用示例
today = date.today().strftime("%Y-%m-%d")
filename = fr"result\{today}_od.csv"
append_column(filename, 'cpu_sale.csv')