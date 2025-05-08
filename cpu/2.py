import pandas as pd
from ast import literal_eval
import re
from datetime import date
import os
def process_cpu_data():
    try:
        today = date.today().strftime("%Y-%m-%d")
        inputname=f"data\{today}_input.csv"
        # 1. 读取数据并清理列名
        df = pd.read_csv(inputname)
        # 列名清洗：移除首尾空格 + 过滤非ASCII字符
        df.columns = [re.sub(r'[^\x00-\x7F]', '', col.strip()) for col in df.columns]
        
        # 2. 动态识别CPU型号列（匹配i3/i5/i7/i9开头，型号格式为数字+可选字母后缀）
        cpu_pattern = r'^i[3579]-\d+[A-Z]*$'
        cpu_columns = [col for col in df.columns if re.match(cpu_pattern, col)]
        
        if not cpu_columns:
            raise ValueError("未检测到有效的CPU型号列，请确认列名格式类似 'i7-8700K'")

        # 3. 转换数据为列表（带异常处理）
        for col in cpu_columns:
            try:
                df[col] = df[col].apply(lambda x: literal_eval(x) if pd.notna(x) else [])
            except (SyntaxError, ValueError) as e:
                raise ValueError(f"列 '{col}' 包含无效数据: {str(e)}")

        # 4. 验证并修复列表长度一致性
        def uniform_length(row):
            """确保同一行所有CPU价格列表长度一致"""
            max_len = max(len(row[col]) for col in cpu_columns)
            return {
                col: (row[col] + [None]*(max_len - len(row[col])))[:max_len]
                for col in cpu_columns
            }

        # 拆分处理保证数据完整性
        original_columns = df.drop(columns=cpu_columns).copy()
        fixed_data = df.apply(uniform_length, axis=1, result_type='expand')
        
        # 重建DataFrame
        df = pd.concat([
            original_columns.reset_index(drop=True),
            fixed_data.reset_index(drop=True)
        ], axis=1)

        # 5. 展开数据
        df = df.explode(cpu_columns, ignore_index=True)
        df=df.iloc[:,2:]
        df=df.dropna()
        # 6. 保存结果
        save_dir = "./data"
        os.makedirs(save_dir, exist_ok=True)
        outputname=os.path.join(save_dir, f"{today}_output.csv")
        df.to_csv(outputname, index=False)
        print(f"数据处理完成，已保存至 {outputname}")
        return True

    except Exception as e:
        print(f"处理失败: {str(e)}")
        return False

# 执行处理
if __name__ == "__main__":
    process_cpu_data()
