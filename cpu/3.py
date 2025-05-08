import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import os
from datetime import date

def iqr_column_cleaner(df, multiplier=1.5):
    """
    对DataFrame的每列进行IQR异常值清洗，返回统计结果和清洗后的DataFrame
    :param df: 输入DataFrame
    :param multiplier: IQR范围乘数，默认1.5
    :return: (统计结果DataFrame, 清洗后的DataFrame)
    """
    results = []
    cleaned_df = df.copy()  # 创建副本用于存储清洗后的数据
    
    for col in df.columns:
        # 跳过非数值列
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"Skipping non-numeric column: {col}")
            continue
            
        data = df[col].values.reshape(-1, 1)
        non_nan_mask = ~np.isnan(data).flatten()  # 非空值掩码
        
        # 计算IQR范围（仅使用非空值）
        if np.sum(non_nan_mask) > 0:
            q1 = np.percentile(data[non_nan_mask], 25)
            q3 = np.percentile(data[non_nan_mask], 75)
            iqr = q3 - q1
            lower_bound = q1 - multiplier * iqr
            upper_bound = q3 + multiplier * iqr
            
            # 标记异常值（仅非空值参与计算）
            valid_values = data[non_nan_mask]
            is_outlier = (valid_values < lower_bound) | (valid_values > upper_bound)
            noise_count = np.sum(is_outlier)
            
            # 将异常值设为NaN
            outlier_indices = np.where(non_nan_mask)[0][is_outlier.flatten()]
            cleaned_df.loc[outlier_indices, col] = np.nan
        else:
            # 全列为空的情况处理
            lower_bound = upper_bound = np.nan
            noise_count = 0
        
        # 计算清洗后的均值
        mean_cleaned = cleaned_df[col].mean()
        
        # 计算分布质量评分
        cleaned_values = cleaned_df[col].dropna().values
        if len(cleaned_values) > 0:
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(cleaned_values.reshape(-1, 1))
            normality_score = np.mean(np.abs(scaled_data) < 2)
        else:
            normality_score = np.nan
        
        results.append({
            'Column': col,
            'Lower_Bound': lower_bound,
            'Upper_Bound': upper_bound,
            'Mean_Cleaned': mean_cleaned,
            'Noise_Count': noise_count,
            'Normality_Score': normality_score
        })
    
    return pd.DataFrame(results), cleaned_df

# 示例使用
if __name__ == "__main__":
    # 读取数据
    today = date.today().strftime("%Y-%m-%d")
    filename = fr"data\{today}_output.csv"
    df = pd.read_csv(filename)
    
    # 执行清洗
    save_dir = "./ana"
    os.makedirs(save_dir, exist_ok=True)
    
    # 获取结果
    stats_df, cleaned_df = iqr_column_cleaner(df, multiplier=1.5)
    
    # 保存统计结果
    stats_filename = os.path.join(save_dir, f"{today}_iqr_stats.csv")
    stats_df.to_csv(stats_filename, index=False)
    
    # 保存清洗后的数据（异常值显示为NaN）
    cleaned_filename = os.path.join(save_dir, f"{today}_iqr.csv")
    cleaned_df.to_csv(cleaned_filename, index=False)
    
    print("统计结果:")
    print(stats_df)
    print("\n清洗后的数据已保存至:", cleaned_filename)