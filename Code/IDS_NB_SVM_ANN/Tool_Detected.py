import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
import shap
import warnings
warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="IDS Testing Interface",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants and configurations

# Define column names and categories
COL_NAMES = ["duration", "protocol_type", "service", "flag", "src_bytes",
             "dst_bytes", "land", "wrong_fragment", "urgent", "hot", "num_failed_logins",
             "logged_in", "num_compromised", "root_shell", "su_attempted", "num_root",
             "num_file_creations", "num_shells", "num_access_files", "num_outbound_cmds",
             "is_host_login", "is_guest_login", "count", "srv_count", "serror_rate",
             "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
             "diff_srv_rate", "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
             "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
             "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
             "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label"]

NUMERIC_COLS = [
    'duration', 'src_bytes', 'dst_bytes', 'wrong_fragment', 'urgent',
    'hot', 'num_failed_logins', 'num_compromised', 'num_root',
    'num_file_creations', 'num_shells', 'num_access_files', 'count',
    'srv_count', 'serror_rate', 'srv_serror_rate', 'rerror_rate',
    'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate', 'srv_diff_host_rate',
    'dst_host_count', 'dst_host_srv_count', 'dst_host_same_srv_rate',
    'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate',
    'dst_host_srv_serror_rate', 'dst_host_rerror_rate',
    'dst_host_srv_rerror_rate'
]

CATEGORICAL_COLS = ['protocol_type', 'service', 'flag']

# Helper Functions
@st.cache_resource
def load_models(model_dir):
    """Load models and preprocessors with caching"""
    try:
        loaded_models = {
            'svm_model': joblib.load(os.path.join(model_dir, 'svm_model.joblib')),
            'nb_model': joblib.load(os.path.join(model_dir, 'nb_model.joblib')),
            'ann_model': joblib.load(os.path.join(model_dir, 'ann_model.joblib')),
            'scaler': joblib.load(os.path.join(model_dir, 'scaler.joblib')),
            'label_encoder': joblib.load(os.path.join(model_dir, 'label_encoder.joblib')),
            'onehot_encoder': joblib.load(os.path.join(model_dir, 'onehot_encoder.joblib'))
        }
        return loaded_models
    except Exception as e:
        st.error(f"Error loading models: {str(e)}")
        return None

def preprocess_test_data(df, models):
    """
    Preprocess test data using the same steps as training data
    """
    try:
        # Add column names if not present
        if df.columns.tolist() == list(range(df.shape[1])):
            df.columns = COL_NAMES

        # Map attacks to categories
        attack_dict = {
            'normal': 'normal',
            'neptune': 'DoS', 'back': 'DoS', 'land': 'DoS', 'pod': 'DoS', 'smurf': 'DoS', 'teardrop': 'DoS',
            'mailbomb': 'DoS', 'apache2': 'DoS', 'processtable': 'DoS', 'udpstorm': 'DoS',
            'ipsweep': 'Probe', 'nmap': 'Probe', 'portsweep': 'Probe', 'satan': 'Probe', 'mscan': 'Probe', 'saint': 'Probe',
            'ftp_write': 'R2L', 'guess_passwd': 'R2L', 'imap': 'R2L', 'multihop': 'R2L', 'phf': 'R2L',
            'spy': 'R2L', 'warezclient': 'R2L', 'warezmaster': 'R2L',
            'buffer_overflow': 'U2R', 'loadmodule': 'U2R', 'perl': 'U2R', 'rootkit': 'U2R', 'sqlattack': 'U2R', 'xterm': 'U2R'
        }

        # Process labels
        df['label'] = df['label'].str.strip().str.rstrip('.')
        df['attack_category'] = df['label'].map(attack_dict)

        # Check for unmapped categories
        unmapped = df['label'][~df['label'].isin(attack_dict.keys())].unique()
        if len(unmapped) > 0:
            st.warning(f"Found unmapped attack types: {unmapped}")
            # Map unmapped to their closest categories or 'unknown'
            for attack in unmapped:
                df.loc[df['label'] == attack, 'attack_category'] = attack_dict.get(attack.lower(), 'unknown')

        # Handle categorical features
        categorical_columns = ['protocol_type', 'service', 'flag']
        missing_cols = [col for col in categorical_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing categorical columns: {missing_cols}")

        # Use saved OneHotEncoder
        cat_enc_test = models['onehot_encoder'].transform(df[categorical_columns])

        # Process numeric features
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        numeric_cols = [col for col in numeric_cols if col not in ['label']]

        if not numeric_cols:
            raise ValueError("No numeric columns found in dataset")

        # Combine features
        X = np.hstack((df[numeric_cols].values, cat_enc_test))

        # Clean data
        if 'attack_category' in df.columns:
            # mask = df['attack_category'] != 'unknown'
            # df = df[mask]
            # X = X[mask]
            
            mask_isna = ~df['attack_category'].isna()
            df = df[mask_isna]
            X = X[mask_isna]

        # Scale features using saved scaler
        X_scaled = models['scaler'].transform(X)

        return X_scaled, df

    except Exception as e:
        st.error(f"Error in preprocessing: {str(e)}")
        st.write("Debug information:")
        st.write("Input columns:", df.columns.tolist())
        st.write("Required columns:", COL_NAMES)
        return None, None

def plot_confusion_matrix(y_true, y_pred, labels):
    """Create interactive confusion matrix plot"""
    cm = confusion_matrix(y_true, y_pred)
    fig = go.Figure(data=go.Heatmap(
        z=cm,
        x=labels,
        y=labels,
        colorscale='Blues',
        text=cm,
        texttemplate="%{text}",
        textfont={"size": 12},
        hoverongaps=False))
    
    fig.update_layout(
        title='Confusion Matrix',
        xaxis_title='Predicted',
        yaxis_title='True',
        width=700,
        height=700,
        xaxis={'side': 'bottom'}
    )
    return fig

def plot_feature_importance(X, model, feature_names, num_features=10):
    """Plot feature importance"""
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importances = np.abs(model.coef_[0])
    else:
        return None
    
    indices = np.argsort(importances)[-num_features:]
    plt.figure(figsize=(10, 6))
    plt.title('Feature Importance')
    plt.barh(range(num_features), importances[indices])
    plt.yticks(range(num_features), [feature_names[i] for i in indices])
    plt.xlabel('Relative Importance')
    return plt

def plot_prediction_analysis(df, predictions, probabilities, models):
    """Plot detailed prediction analysis"""
    st.subheader("Prediction Analysis")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Predictions", "Feature Importance", "Data Distribution"])
    
    with tab1:
        # Prediction distribution
        fig = px.pie(
            names=models['label_encoder'].inverse_transform(np.unique(predictions)), 
            values=np.bincount(predictions),
            title="Distribution of Predictions"
        )
        st.plotly_chart(fig)
        
        # Confidence scores
        fig = px.box(
            y=np.max(probabilities, axis=1),
            title="Prediction Confidence Distribution"
        )
        st.plotly_chart(fig)
    
    with tab2:
        # Select features to analyze
        selected_features = st.multiselect(
            "Select features to analyze",
            NUMERIC_COLS,
            default=NUMERIC_COLS[:5]
        )
        
        if selected_features:
            fig = px.box(
                df[selected_features],
                title="Feature Value Distribution"
            )
            st.plotly_chart(fig)
            
            # Feature correlation
            corr = df[selected_features].corr()
            fig = px.imshow(
                corr,
                title="Feature Correlation Matrix"
            )
            st.plotly_chart(fig)
    
    with tab3:
        # Data distribution analysis
        selected_feature = st.selectbox(
            "Select feature for detailed analysis",
            NUMERIC_COLS
        )
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(
                df[selected_feature],
                title=f"Distribution of {selected_feature}"
            )
            st.plotly_chart(fig)
        
        with col2:
            fig = px.box(
                df[selected_feature],
                title=f"Box Plot of {selected_feature}"
            )
            st.plotly_chart(fig)

def analyze_predictions(df, results_df, X_scaled):
    """Phân tích chi tiết các dự đoán đúng/sai"""
    st.header("Chi tiết dự đoán đúng/sai")
    
    # Xác định dự đoán đúng/sai
    correct_mask = results_df['Predicted'] == results_df['Actual']
    incorrect_mask = ~correct_mask
    
    # Tạo DataFrame cho phân tích
    analysis_df = pd.DataFrame()
    
    # Thêm các features gốc
    for col in NUMERIC_COLS:
        analysis_df[f'original_{col}'] = df[col]
    
    # Thêm các features đã scale
    for i, col in enumerate(NUMERIC_COLS):
        analysis_df[f'scaled_{col}'] = X_scaled[:, i]
    
    # Thêm kết quả dự đoán
    analysis_df['predicted'] = results_df['Predicted']
    analysis_df['actual'] = results_df['Actual']
    analysis_df['is_correct'] = correct_mask
    
    # Tạo tabs cho phân tích
    tab1, tab2, tab3 = st.tabs(["So sánh Features", "Chi tiết Samples", "Statistical Analysis"])
    
    with tab1:
        st.subheader("So sánh Features giữa dự đoán đúng và sai")
        
        # Chọn features để phân tích
        feature_type = st.radio(
            "Chọn loại features",
            ["Original Features", "Scaled Features"]
        )
        
        prefix = "original_" if feature_type == "Original Features" else "scaled_"
        selected_features = st.multiselect(
            "Chọn features để so sánh",
            NUMERIC_COLS,
            default=NUMERIC_COLS[:5]
        )
        
        # Tạo box plots cho từng feature
        for feature in selected_features:
            fig = go.Figure()
            
            # Box plot cho dự đoán đúng
            fig.add_trace(go.Box(
                y=analysis_df[prefix + feature][correct_mask],
                name="Correct Predictions",
                boxpoints='outliers'
            ))
            
            # Box plot cho dự đoán sai
            fig.add_trace(go.Box(
                y=analysis_df[prefix + feature][incorrect_mask],
                name="Incorrect Predictions",
                boxpoints='outliers'
            ))
            
            fig.update_layout(
                title=f"{feature} Distribution",
                yaxis_title=feature,
                boxmode='group'
            )
            st.plotly_chart(fig)
    
    with tab2:
        st.subheader("Chi tiết từng mẫu")
        
        # Filter options
        prediction_filter = st.selectbox(
            "Filter by prediction result",
            ["All", "Correct Predictions", "Incorrect Predictions"]
        )
        
        if prediction_filter == "Correct Predictions":
            samples = analysis_df[correct_mask]
        elif prediction_filter == "Incorrect Predictions":
            samples = analysis_df[incorrect_mask]
        else:
            samples = analysis_df
        
        # Hiển thị samples
        st.write("Selected Samples:")
        st.dataframe(samples[['predicted', 'actual', 'is_correct'] + 
                           [f'original_{col}' for col in selected_features]])
        
        # Chi tiết từng mẫu
        if st.checkbox("Show Detailed Sample Analysis"):
            sample_idx = st.selectbox(
                "Select sample to analyze",
                range(len(samples))
            )
            
            selected_sample = samples.iloc[sample_idx]
            
            # Hiển thị chi tiết
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Original Features:")
                orig_features = {col: selected_sample[f'original_{col}'] 
                               for col in NUMERIC_COLS}
                st.write(pd.Series(orig_features))
            
            with col2:
                st.write("Scaled Features:")
                scaled_features = {col: selected_sample[f'scaled_{col}'] 
                                 for col in NUMERIC_COLS}
                st.write(pd.Series(scaled_features))
    
    with tab3:
        st.subheader("Statistical Analysis")
        
        # Tính toán thống kê cho từng feature
        stats_df = pd.DataFrame()
        
        for feature in selected_features:
            # Stats cho dự đoán đúng
            correct_stats = analysis_df[prefix + feature][correct_mask].describe()
            incorrect_stats = analysis_df[prefix + feature][incorrect_mask].describe()
            
            stats_df[f'{feature}_correct'] = correct_stats
            stats_df[f'{feature}_incorrect'] = incorrect_stats
        
        st.write("Statistical Summary:")
        st.dataframe(stats_df)
        
        # Correlation analysis
        st.write("Correlation Analysis:")
        correlation = analysis_df[[prefix + col for col in selected_features]].corr()
        fig = px.imshow(correlation, title="Feature Correlation Matrix")
        st.plotly_chart(fig)

def main():
    st.title("🛡️ Intrusion Detection System Testing Interface")
    
    # Load models
    model_path = "models/latest"
    if not os.path.exists(model_path):
        st.error(f"Model directory not found: {model_path}")
        return
    
    with st.spinner("Loading models..."):
        models = load_models(model_path)
    
    if not models:
        return
    
    # Model selection
    model_options = {
        'Support Vector Machine': 'svm_model',
        'Naive Bayes': 'nb_model',
        'Neural Network': 'ann_model'
    }
    selected_model = st.sidebar.selectbox("Select Model", list(model_options.keys()))
    
    # File upload
    uploaded_file = st.file_uploader("Upload test data (CSV)", type=['csv'])
    
    if uploaded_file:
        try:
            # Load data
            df = pd.read_csv(uploaded_file, header=None, names=COL_NAMES)
            st.write("Data loaded successfully:", df.shape)
            
            # Preprocess data
            with st.spinner("Processing data..."):
                X_scaled, processed_df = preprocess_test_data(df, models)
            
            if X_scaled is not None:
                # Make predictions
                model = models[model_options[selected_model]]
                predictions = model.predict(X_scaled)
                probabilities = model.predict_proba(X_scaled)
                
                # Show results
                st.header("Results")
                results_df = pd.DataFrame({
                    'Predicted': models['label_encoder'].inverse_transform(predictions),
                    'Confidence': np.max(probabilities, axis=1)
                })
                
                if 'label' in processed_df.columns:
                    # Thay vì dùng trực tiếp label, sử dụng attack_category đã được map
                    results_df['Actual'] = processed_df['attack_category']
                    accuracy = (results_df['Predicted'] == results_df['Actual']).mean()
                    st.metric("Model Accuracy", f"{accuracy:.2%}")
                
                # Display results
                st.dataframe(results_df)
                
                # Hiển thị phân tích chi tiết
                analyze_predictions(df, results_df, X_scaled)
                
                # Original visualizations
                plot_prediction_analysis(processed_df, predictions, probabilities, models)
                
                # Feature importance
                if st.checkbox("Show Feature Importance"):
                    features = (
                        list(NUMERIC_COLS) + 
                        [f"{col}_{val}" for col, vals in 
                         zip(CATEGORICAL_COLS, models['onehot_encoder'].categories_) 
                         for val in vals]
                    )
                    
                    importance_fig = plot_feature_importance(
                        X_scaled, 
                        model,
                        features
                    )
                    if importance_fig:
                        st.pyplot(importance_fig)
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.write("Please ensure your input file matches the expected format.")

if __name__ == "__main__":
    main()