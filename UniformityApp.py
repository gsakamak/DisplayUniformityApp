import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import make_interp_spline
import plotly.graph_objects as go
import plotly.express as px

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(page_title="Display Uniformity Analysis", layout="wide")

# ==========================================
# Login System
# ==========================================
# セッションステートでログイン状態を管理
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# ログインしていない場合はログイン画面を表示
if not st.session_state['logged_in']:
    st.title("Login")
    st.markdown("Please log in to access the Display Uniformity Analysis tool.")
    
    with st.form("login_form"):
        # 【変更箇所】「(Email Address)」の表記を削除
        user_id = st.text_input("ID")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            # ログイン条件: IDが @yitoa.co.jp で終わり、パスワードがIDと完全に一致すること
            if user_id.endswith("@yitoa.co.jp") and user_id == password:
                st.session_state['logged_in'] = True
                st.success("Login successful!")
                st.rerun() # 画面をリロードしてメインコンテンツを表示
            else:
                st.error("Invalid ID or Password.")
                
    # ログイン画面表示時はここで処理を停止し、メインコンテンツは表示させない
    st.stop()

# ==========================================
# Sidebar Settings (Logged in content)
# ==========================================
# 1. Logo Display
try:
    st.sidebar.image("yitoa.png", width='stretch')
except FileNotFoundError:
    st.sidebar.warning("Logo 'yitoa.png' not found. Please place it in the same directory.")

# 2. Copyright Information (Centered)
st.sidebar.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 14px;'>
        <p style='margin-bottom: 0;'>Copyright(c) YITOA Technology.</p>
        <p>All rights reserved.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ログアウトボタン
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("Configuration")

# 3. Grid Size Input
st.sidebar.subheader("Measurement Grid")
grid_cols = st.sidebar.number_input("Horizontal Points (X)", min_value=1, value=9, step=1)
grid_rows = st.sidebar.number_input("Vertical Points (Y)", min_value=1, value=15, step=1)

# Display Total Measurement Points
total_points = grid_cols * grid_rows
st.sidebar.markdown(f"**Total Measurement Points:** `{total_points}`")

# 4. Y-axis Range Settings (Luminance)
st.sidebar.markdown("---")
st.sidebar.subheader("Y-axis Range (Luminance)")
auto_range_y = st.sidebar.checkbox("Auto Range (Luminance)", value=True)

y_min_input = 0.0
y_max_input = 600.0

if not auto_range_y:
    y_min_input = st.sidebar.number_input("Luminance Minimum", value=0.0, step=10.0)
    y_max_input = st.sidebar.number_input("Luminance Maximum", value=600.0, step=10.0)

# 5. Y-axis Range Settings (Delta u'v')
st.sidebar.markdown("---")
st.sidebar.subheader("Y-axis Range (Delta u'v')")
auto_range_duv = st.sidebar.checkbox("Auto Range (Delta u'v')", value=True)

duv_min_input = 0.0
duv_max_input = 0.05

if not auto_range_duv:
    duv_min_input = st.sidebar.number_input("Delta u'v' Minimum", value=0.0, step=0.001, format="%.4f")
    duv_max_input = st.sidebar.number_input("Delta u'v' Maximum", value=0.05, step=0.001, format="%.4f")

# 6. Heatmap Range Settings (Luminance)
st.sidebar.markdown("---")
st.sidebar.subheader("Heatmap Range (Luminance)")
auto_range_hm_lum = st.sidebar.checkbox("Auto Range Heatmap (Luminance)", value=True)

hm_lum_min_input = 0.0
hm_lum_max_input = 600.0

if not auto_range_hm_lum:
    hm_lum_min_input = st.sidebar.number_input("Heatmap Luminance Minimum", value=0.0, step=10.0)
    hm_lum_max_input = st.sidebar.number_input("Heatmap Luminance Maximum", value=600.0, step=10.0)

# 7. Heatmap Range Settings (Delta u'v')
st.sidebar.markdown("---")
st.sidebar.subheader("Heatmap Range (Delta u'v')")
auto_range_hm_duv = st.sidebar.checkbox("Auto Range Heatmap (Delta u'v')", value=True)

hm_duv_min_input = 0.0
hm_duv_max_input = 0.05

if not auto_range_hm_duv:
    hm_duv_min_input = st.sidebar.number_input("Heatmap Delta u'v' Minimum", value=0.0, step=0.001, format="%.4f")
    hm_duv_max_input = st.sidebar.number_input("Heatmap Delta u'v' Maximum", value=0.05, step=0.001, format="%.4f")

# 8. Heatmap Size Settings
st.sidebar.markdown("---")
st.sidebar.subheader("Heatmap Size")
heatmap_width = st.sidebar.slider("Width", min_value=1.0, max_value=5.8, value=2.9, step=0.1)
heatmap_height = st.sidebar.slider("Height", min_value=1.7, max_value=8.0, value=4.0, step=0.1)

# 9. Display Options (Toggle Graphs & Average Line)
st.sidebar.markdown("---")
st.sidebar.subheader("Display Options")
show_row_avg = st.sidebar.checkbox("Show Row Average Line", value=True)
show_plot_lum_h = st.sidebar.checkbox("Show Luminance Chart (Horizontal)", value=True)
show_plot_lum_v = st.sidebar.checkbox("Show Luminance Chart (Vertical)", value=True)
show_plot_duv_h = st.sidebar.checkbox("Show Delta u'v' Chart (Horizontal)", value=True)
show_plot_duv_v = st.sidebar.checkbox("Show Delta u'v' Chart (Vertical)", value=True)
show_plot_heatmap_lum = st.sidebar.checkbox("Show Heatmap (Luminance)", value=True)
show_plot_heatmap_duv = st.sidebar.checkbox("Show Heatmap (Delta u'v')", value=True)
show_heatmap_annot = st.sidebar.checkbox("Show Heatmap Data Labels", value=True)

# 10. File Uploader (Multiple files support)
st.sidebar.markdown("---")
st.sidebar.subheader("Data Upload")
uploaded_files = st.sidebar.file_uploader("Upload Uniformity CSV", type=['csv'], accept_multiple_files=True)

# 11. Select Files to Display
if uploaded_files:
    file_names = [f.name for f in uploaded_files]
    selected_file_names = st.sidebar.multiselect("Select Files to Display", file_names, default=file_names)
    selected_files = [f for f in uploaded_files if f.name in selected_file_names]
else:
    selected_files = []

# ==========================================
# Main Content
# ==========================================
st.title("Display Uniformity Analysis")
st.markdown("Analyze display luminance and color uniformity based on the uploaded measurement data.")

def load_data(file):
    content = file.getvalue().decode('utf-8', errors='replace').splitlines()
    header_idx = 0
    for i, line in enumerate(content):
        if line.startswith('Name'):
            header_idx = i
            break
    
    file.seek(0)
    df = pd.read_csv(file, skiprows=header_idx)
    df.columns = df.columns.str.strip()
    return df

if selected_files:
    processed_data = []
    has_error = False
    
    # Process all selected files
    for file in selected_files:
        try:
            df = load_data(file)
            
            required_cols = ['Name', 'Y', 'x', 'y']
            if not all(col in df.columns for col in required_cols):
                st.error(f"The uploaded CSV '{file.name}' must contain the following columns: {', '.join(required_cols)}")
                has_error = True
                continue
                
            denominator = -2 * df['x'] + 12 * df['y'] + 3
            df['u_prime'] = (4 * df['x']) / denominator
            df['v_prime'] = (9 * df['y']) / denominator
            
            center_x = grid_cols // 2
            center_y = grid_rows // 2
            center_idx = center_y * grid_cols + center_x
            
            if center_idx < len(df):
                u_ref = df.loc[center_idx, 'u_prime']
                v_ref = df.loc[center_idx, 'v_prime']
                ref_name = df.loc[center_idx, 'Name']
            else:
                u_ref = df.loc[0, 'u_prime']
                v_ref = df.loc[0, 'v_prime']
                ref_name = df.loc[0, 'Name']
                
            df['delta_u_v'] = np.sqrt((df['u_prime'] - u_ref)**2 + (df['v_prime'] - v_ref)**2)
            
            # Horizontal Averages
            df['Row_Index'] = df.index // grid_cols
            df['Row_Avg_Y'] = df.groupby('Row_Index')['Y'].transform('mean')
            df['Row_Avg_duv'] = df.groupby('Row_Index')['delta_u_v'].transform('mean')
            
            # Vertical Averages
            df['Col_Index'] = df.index % grid_cols
            df_vertical = df.sort_values(by=['Col_Index', 'Row_Index']).reset_index(drop=True)
            df_vertical['Col_Avg_Y'] = df_vertical.groupby('Col_Index')['Y'].transform('mean')
            df_vertical['Col_Avg_duv'] = df_vertical.groupby('Col_Index')['delta_u_v'].transform('mean')
            
            # Horizontal Approximation
            row_centers = df.groupby('Row_Index')['Name'].mean().values
            row_avg_y_vals = df.groupby('Row_Index')['Y'].mean().values
            row_avg_duv_vals = df.groupby('Row_Index')['delta_u_v'].mean().values
            x_smooth = np.linspace(df['Name'].min(), df['Name'].max(), 300)
            if len(row_centers) > 1:
                k = 3 if len(row_centers) > 3 else 1
                spl_y = make_interp_spline(row_centers, row_avg_y_vals, k=k)
                y_smooth = spl_y(x_smooth)
                spl_duv = make_interp_spline(row_centers, row_avg_duv_vals, k=k)
                duv_smooth = spl_duv(x_smooth)
            else:
                x_smooth = df['Name']
                y_smooth = df['Row_Avg_Y']
                duv_smooth = df['Row_Avg_duv']
                
            # Vertical Approximation
            col_centers = df_vertical.reset_index().groupby('Col_Index')['index'].mean().values
            col_avg_y_vals = df_vertical.groupby('Col_Index')['Y'].mean().values
            col_avg_duv_vals = df_vertical.groupby('Col_Index')['delta_u_v'].mean().values
            x_smooth_v = np.linspace(0, len(df_vertical) - 1, 300)
            if len(col_centers) > 1:
                k_v = 3 if len(col_centers) > 3 else 1
                spl_y_v = make_interp_spline(col_centers, col_avg_y_vals, k=k_v)
                y_smooth_v = spl_y_v(x_smooth_v)
                spl_duv_v = make_interp_spline(col_centers, col_avg_duv_vals, k=k_v)
                duv_smooth_v = spl_duv_v(x_smooth_v)
            else:
                x_smooth_v = np.arange(len(df_vertical))
                y_smooth_v = df_vertical['Col_Avg_Y']
                duv_smooth_v = df_vertical['Col_Avg_duv']
            
            processed_data.append({
                'file_name': file.name, 'df': df, 'df_vertical': df_vertical,
                'ref_name': ref_name, 'x_smooth': x_smooth, 'y_smooth': y_smooth,
                'duv_smooth': duv_smooth, 'x_smooth_v': x_smooth_v,
                'y_smooth_v': y_smooth_v, 'duv_smooth_v': duv_smooth_v
            })
            
        except Exception as e:
            st.error(f"Error processing the file '{file.name}': {e}")
            has_error = True

    if processed_data and not has_error:
        st.success(f"{len(processed_data)} file(s) loaded successfully!")
        
        with st.expander("Show Raw Data"):
            for data in processed_data:
                st.markdown(f"**{data['file_name']}**")
                st.dataframe(data['df'].head())
        
        # Color palette for Plotly lines
        plotly_colors = px.colors.qualitative.Plotly

        # =========================================================
        # 1. Luminance Graphs (Horizontal & Vertical Side-by-Side)
        # =========================================================
        col_lum1, col_lum2 = st.columns(2)
        
        with col_lum1:
            if show_plot_lum_h:
                st.subheader("1-A. Luminance by Measurement Position (Horizontal)")
                fig1 = go.Figure()
                
                for idx, data in enumerate(processed_data):
                    c = plotly_colors[idx % len(plotly_colors)]
                    
                    fig1.add_trace(go.Scatter(
                        x=data['df']['Name'], y=data['df']['Y'], 
                        mode='lines+markers', name=data['file_name'],
                        line=dict(color=c), marker=dict(size=6)
                    ))
                    
                    if show_row_avg:
                        fig1.add_trace(go.Scatter(
                            x=data['x_smooth'], y=data['y_smooth'], mode='lines', 
                            line=dict(color=c, dash='dash', width=1.5), opacity=0.5, 
                            showlegend=False, hoverinfo='skip'
                        ))
                
                fig1.update_layout(
                    title='Luminance Distribution Line Chart (Horizontal)',
                    xaxis_title='Measurement Position (Name)',
                    yaxis_title='Luminance (Y) [nit]',
                    hovermode='x unified',
                    margin=dict(l=40, r=40, t=40, b=80),
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5)
                )
                
                if not auto_range_y:
                    if y_min_input < y_max_input:
                        fig1.update_yaxes(range=[y_min_input, y_max_input])
                    else:
                        st.error("Luminance: Minimum must be less than Maximum.")
                
                st.plotly_chart(fig1, width='stretch')

        with col_lum2:
            if show_plot_lum_v:
                st.subheader("1-B. Luminance by Measurement Position (Vertical)")
                fig1v = go.Figure()
                
                for idx, data in enumerate(processed_data):
                    c = plotly_colors[idx % len(plotly_colors)]
                    df_v = data['df_vertical']
                    x_vals = np.arange(len(df_v))
                    
                    # カスタムホバーテキスト（元のName値を表示）
                    hover_texts = [f"Name: {name}<br>Y: {val:.2f}" for name, val in zip(df_v['Name'], df_v['Y'])]
                    
                    fig1v.add_trace(go.Scatter(
                        x=x_vals, y=df_v['Y'], mode='lines+markers', name=data['file_name'],
                        line=dict(color=c), marker=dict(size=6),
                        text=hover_texts, hoverinfo='text+name'
                    ))
                    
                    if show_row_avg:
                        fig1v.add_trace(go.Scatter(
                            x=data['x_smooth_v'], y=data['y_smooth_v'], mode='lines', 
                            line=dict(color=c, dash='dash', width=1.5), opacity=0.5, 
                            showlegend=False, hoverinfo='skip'
                        ))
                
                if len(processed_data) > 0:
                    df_v0 = processed_data[0]['df_vertical']
                    if len(df_v0) > 0:
                        num_ticks = min(20, len(df_v0))
                        tick_indices = np.linspace(0, len(df_v0)-1, num_ticks, dtype=int)
                        tick_labels = df_v0['Name'].iloc[tick_indices].astype(str).tolist()
                        fig1v.update_xaxes(tickmode='array', tickvals=tick_indices, ticktext=tick_labels, tickangle=45)
                
                fig1v.update_layout(
                    title='Luminance Distribution Line Chart (Vertical)',
                    xaxis_title='Measurement Position (Name)',
                    yaxis_title='Luminance (Y) [nit]',
                    hovermode='closest',
                    margin=dict(l=40, r=40, t=40, b=80),
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5)
                )
                
                if not auto_range_y:
                    fig1v.update_yaxes(range=[y_min_input, y_max_input])
                
                st.plotly_chart(fig1v, width='stretch')
            
        # --- 統計値の表示 (Luminance) ---
        if show_plot_lum_h or show_plot_lum_v:
            lum_stats = []
            for data in processed_data:
                y_vals = data['df']['Y']
                y_avg = y_vals.mean()
                y_max = y_vals.max()
                y_min = y_vals.min()
                y_delta = y_max - y_min
                y_uniformity = (y_min / y_max * 100) if y_max != 0 else 0
                
                lum_stats.append({
                    "File Name": data['file_name'],
                    "Average": f"{y_avg:.2f}",
                    "Max": f"{y_max:.2f}",
                    "Min": f"{y_min:.2f}",
                    "Delta (Max-Min)": f"{y_delta:.2f}",
                    "Uniformity (%)": f"{y_uniformity:.2f}%"
                })
            
            st.markdown("##### Statistics: Luminance (Y)")
            st.table(pd.DataFrame(lum_stats).set_index("File Name"))

        # =========================================================
        # 2. Delta u'v' Graphs (Horizontal & Vertical Side-by-Side)
        # =========================================================
        col_duv1, col_duv2 = st.columns(2)
        
        with col_duv1:
            if show_plot_duv_h:
                st.subheader("2-A. Color Difference (Delta u'v') (Horizontal)")
                ref_name_disp = processed_data[0]['ref_name']
                st.markdown(rf"*Reference point for $\Delta u'v'$ calculation is the center position (Name: {ref_name_disp}).*")
                
                fig2 = go.Figure()
                for idx, data in enumerate(processed_data):
                    c = plotly_colors[idx % len(plotly_colors)]
                    
                    fig2.add_trace(go.Scatter(
                        x=data['df']['Name'], y=data['df']['delta_u_v'], 
                        mode='lines+markers', name=data['file_name'],
                        line=dict(color=c), marker=dict(size=6)
                    ))
                    
                    if show_row_avg:
                        fig2.add_trace(go.Scatter(
                            x=data['x_smooth'], y=data['duv_smooth'], mode='lines', 
                            line=dict(color=c, dash='dash', width=1.5), opacity=0.5, 
                            showlegend=False, hoverinfo='skip'
                        ))
                
                fig2.update_layout(
                    title=r"Color Difference (Delta u'v') Line Chart (Horizontal)",
                    xaxis_title='Measurement Position (Name)',
                    yaxis_title="Delta u'v'",
                    hovermode='x unified',
                    margin=dict(l=40, r=40, t=40, b=80),
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5)
                )
                
                if not auto_range_duv:
                    if duv_min_input < duv_max_input:
                        fig2.update_yaxes(range=[duv_min_input, duv_max_input])
                    else:
                        st.error("Delta u'v': Minimum must be less than Maximum.")
                
                st.plotly_chart(fig2, width='stretch')

        with col_duv2:
            if show_plot_duv_v:
                st.subheader("2-B. Color Difference (Delta u'v') (Vertical)")
                st.markdown(r"&nbsp;") # 高さ合わせ
                
                fig2v = go.Figure()
                for idx, data in enumerate(processed_data):
                    c = plotly_colors[idx % len(plotly_colors)]
                    df_v = data['df_vertical']
                    x_vals = np.arange(len(df_v))
                    
                    hover_texts = [f"Name: {name}<br>Delta u'v': {val:.4f}" for name, val in zip(df_v['Name'], df_v['delta_u_v'])]
                    
                    fig2v.add_trace(go.Scatter(
                        x=x_vals, y=df_v['delta_u_v'], mode='lines+markers', name=data['file_name'],
                        line=dict(color=c), marker=dict(size=6),
                        text=hover_texts, hoverinfo='text+name'
                    ))
                    
                    if show_row_avg:
                        fig2v.add_trace(go.Scatter(
                            x=data['x_smooth_v'], y=data['duv_smooth_v'], mode='lines', 
                            line=dict(color=c, dash='dash', width=1.5), opacity=0.5, 
                            showlegend=False, hoverinfo='skip'
                        ))
                
                if len(processed_data) > 0:
                    df_v0 = processed_data[0]['df_vertical']
                    if len(df_v0) > 0:
                        num_ticks = min(20, len(df_v0))
                        tick_indices = np.linspace(0, len(df_v0)-1, num_ticks, dtype=int)
                        tick_labels = df_v0['Name'].iloc[tick_indices].astype(str).tolist()
                        fig2v.update_xaxes(tickmode='array', tickvals=tick_indices, ticktext=tick_labels, tickangle=45)
                
                fig2v.update_layout(
                    title=r"Color Difference (Delta u'v') Line Chart (Vertical)",
                    xaxis_title='Measurement Position (Name)',
                    yaxis_title="Delta u'v'",
                    hovermode='closest',
                    margin=dict(l=40, r=40, t=40, b=80),
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5)
                )
                
                if not auto_range_duv:
                    fig2v.update_yaxes(range=[duv_min_input, duv_max_input])
                
                st.plotly_chart(fig2v, width='stretch')

        # --- 統計値の表示 (Delta u'v') ---
        if show_plot_duv_h or show_plot_duv_v:
            duv_stats = []
            for data in processed_data:
                duv_vals = data['df']['delta_u_v']
                duv_avg = duv_vals.mean()
                duv_max = duv_vals.max()
                duv_min = duv_vals.min()
                duv_delta = duv_max - duv_min
                
                u_vals = data['df']['u_prime'].to_numpy()
                v_vals = data['df']['v_prime'].to_numpy()
                u_diff = u_vals[:, np.newaxis] - u_vals[np.newaxis, :]
                v_diff = v_vals[:, np.newaxis] - v_vals[np.newaxis, :]
                color_uniformity = np.nanmax(np.sqrt(u_diff**2 + v_diff**2))
                
                duv_stats.append({
                    "File Name": data['file_name'],
                    "Average": f"{duv_avg:.4f}",
                    "Max": f"{duv_max:.4f}",
                    "Min": f"{duv_min:.4f}",
                    "Delta (Max-Min)": f"{duv_delta:.4f}",
                    "Color Uniformity": f"{color_uniformity:.4f}"
                })
            
            st.markdown("##### Statistics: Delta u'v'")
            st.table(pd.DataFrame(duv_stats).set_index("File Name"))
        
        # =========================================================
        # 3. Heatmaps (Luminance & Delta u'v' Side-by-Side)
        # =========================================================
        if show_plot_heatmap_lum or show_plot_heatmap_duv:
            st.subheader("3. 2D Uniformity Maps")
            st.markdown("Position 1 is at the top-left, counting up horizontally.")
            
            # Plotlyのサイズ設定 (スライダー値からピクセルに変換)
            px_width = int(heatmap_width * 160)
            px_height = int(heatmap_height * 160)
            scale_factor = min(heatmap_width / 2.1, heatmap_height / 3.5)
            annot_font_size = max(8, 12 * scale_factor)
            
            for data in processed_data:
                df_hm = data['df']
                if len(df_hm) >= total_points:
                    st.markdown(f"**File: {data['file_name']}**")
                    
                    hm_col1, hm_col2 = st.columns(2)
                    
                    # --- Plot 3-A: 2D Uniformity Heatmap (Luminance) ---
                    if show_plot_heatmap_lum:
                        with hm_col1:
                            luminance_data = df_hm['Y'].values[:total_points]
                            heatmap_data_lum = luminance_data.reshape((grid_rows, grid_cols))
                            
                            zmin_lum = hm_lum_min_input if not auto_range_hm_lum else None
                            zmax_lum = hm_lum_max_input if not auto_range_hm_lum else None
                            
                            kwargs_lum = {}
                            if show_heatmap_annot:
                                kwargs_lum['text'] = np.round(heatmap_data_lum, 1)
                                kwargs_lum['texttemplate'] = "%{text:.1f}"
                            
                            fig3 = go.Figure(data=go.Heatmap(
                                z=heatmap_data_lum,
                                x=list(range(1, grid_cols + 1)),
                                y=list(range(1, grid_rows + 1)),
                                colorscale='Viridis',
                                zmin=zmin_lum, zmax=zmax_lum,
                                hoverinfo="x+y+z",
                                colorbar=dict(title='Luminance (Y)', thickness=20),
                                **kwargs_lum
                            ))
                            
                            if show_heatmap_annot:
                                fig3.update_traces(textfont=dict(size=annot_font_size))
                                
                            fig3.update_xaxes(title="Horizontal Points (X)", tickmode='linear', dtick=1)
                            # y軸を反転させて元のmatplotlibと同じく左上を原点にする
                            fig3.update_yaxes(title="Vertical Points (Y)", tickmode='linear', dtick=1, autorange='reversed')
                            
                            fig3.update_layout(
                                title=f"Heatmap (Luminance)",
                                width=px_width, height=px_height,
                                margin=dict(l=40, r=130, t=40, b=40)
                            )
                            st.plotly_chart(fig3, width='content')
                            
                    # --- Plot 3-B: 2D Uniformity Heatmap (Delta u'v') ---
                    if show_plot_heatmap_duv:
                        with hm_col2:
                            duv_data = df_hm['delta_u_v'].values[:total_points]
                            heatmap_data_duv = duv_data.reshape((grid_rows, grid_cols))
                            
                            zmin_duv = hm_duv_min_input if not auto_range_hm_duv else None
                            zmax_duv = hm_duv_max_input if not auto_range_hm_duv else None
                            
                            kwargs_duv = {}
                            if show_heatmap_annot:
                                kwargs_duv['text'] = np.round(heatmap_data_duv, 4)
                                kwargs_duv['texttemplate'] = "%{text:.4f}"
                            
                            fig4 = go.Figure(data=go.Heatmap(
                                z=heatmap_data_duv,
                                x=list(range(1, grid_cols + 1)),
                                y=list(range(1, grid_rows + 1)),
                                colorscale='Viridis',
                                zmin=zmin_duv, zmax=zmax_duv,
                                hoverinfo="x+y+z",
                                colorbar=dict(title="Delta u'v'", thickness=20),
                                **kwargs_duv
                            ))
                            
                            if show_heatmap_annot:
                                fig4.update_traces(textfont=dict(size=annot_font_size))
                                
                            fig4.update_xaxes(title="Horizontal Points (X)", tickmode='linear', dtick=1)
                            fig4.update_yaxes(title="Vertical Points (Y)", tickmode='linear', dtick=1, autorange='reversed')
                            
                            fig4.update_layout(
                                title=f"Heatmap (Delta u'v')",
                                width=px_width, height=px_height,
                                margin=dict(l=40, r=130, t=40, b=40)
                            )
                            st.plotly_chart(fig4, width='content')
                else:
                    st.warning(f"Warning: The grid size ({grid_cols}x{grid_rows} = {total_points} points) requires more data points than the CSV '{data['file_name']}' contains ({len(df_hm)} points). Heatmap cannot be generated.")
            
            # --- 統計値の表示 (Heatmapの下に追加) ---
            if show_plot_heatmap_lum:
                lum_stats_hm = []
                for data in processed_data:
                    y_vals = data['df']['Y']
                    y_avg = y_vals.mean()
                    y_max = y_vals.max()
                    y_min = y_vals.min()
                    y_delta = y_max - y_min
                    y_uniformity = (y_min / y_max * 100) if y_max != 0 else 0
                    
                    lum_stats_hm.append({
                        "File Name": data['file_name'],
                        "Average": f"{y_avg:.2f}",
                        "Max": f"{y_max:.2f}",
                        "Min": f"{y_min:.2f}",
                        "Delta (Max-Min)": f"{y_delta:.2f}",
                        "Uniformity (%)": f"{y_uniformity:.2f}%"
                    })
                
                st.markdown("##### Statistics: Luminance (Y)")
                st.table(pd.DataFrame(lum_stats_hm).set_index("File Name"))

            if show_plot_heatmap_duv:
                duv_stats_hm = []
                for data in processed_data:
                    duv_vals = data['df']['delta_u_v']
                    duv_avg = duv_vals.mean()
                    duv_max = duv_vals.max()
                    duv_min = duv_vals.min()
                    duv_delta = duv_max - duv_min
                    
                    u_vals = data['df']['u_prime'].to_numpy()
                    v_vals = data['df']['v_prime'].to_numpy()
                    u_diff = u_vals[:, np.newaxis] - u_vals[np.newaxis, :]
                    v_diff = v_vals[:, np.newaxis] - v_vals[np.newaxis, :]
                    color_uniformity = np.nanmax(np.sqrt(u_diff**2 + v_diff**2))
                    
                    duv_stats_hm.append({
                        "File Name": data['file_name'],
                        "Average": f"{duv_avg:.4f}",
                        "Max": f"{duv_max:.4f}",
                        "Min": f"{duv_min:.4f}",
                        "Delta (Max-Min)": f"{duv_delta:.4f}",
                        "Color Uniformity": f"{color_uniformity:.4f}"
                    })
                
                st.markdown("##### Statistics: Delta u'v'")
                st.table(pd.DataFrame(duv_stats_hm).set_index("File Name"))
            
else:
    st.info("Please upload one or more CSV files from the sidebar to begin analysis.")