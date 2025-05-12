# 🏘️ Real Estate Price Prediction and Model Benchmarking in Rio de Janeiro

## 📌 Problem Motivation

In recent years, finding affordable housing has become increasingly difficult for the newer generation. Compared to previous decades, today's urban populations face inflated real estate prices and limited availability. Compounding this issue are platforms like Airbnb, which have further driven up housing costs in major cities.

Although many online platforms offer property data, there's a growing need for **data-backed decision-making**. With an overwhelming amount of available information, individuals who know how to extract valuable insights from data gain a significant advantage.

## 🧠 Problem Context

While traditional methods like **linear regression** have long been used for price estimation, they fall short in capturing **non-linear** and **complex relationships** present in real estate data. Machine learning approaches — particularly **ensemble methods**, **neural networks**, and **embedding-based models** — offer an alternative by uncovering hidden patterns and increasing predictive accuracy.

However, there is no single "best" algorithm. Model performance depends on **data quality**, **quantity**, and **available computational resources**.

### 🔍 Hypotheses

1. **Hypothesis 1**: Deep neural networks and embedding-based models offer superior predictive performance compared to simpler models like linear regression.
2. **Hypothesis 2**: Models can generalize well if relevant features (property structure, location, nearby infrastructure) are properly included during training.

### 🎯 Objectives

#### General Objective
- Compare the predictive performance of different supervised learning models in the context of real estate pricing.

#### Specific Objectives
- Collect and prepare a rich dataset of real estate listings
- Train and optimize multiple regression models
- Analyze and interpret performance metrics to identify the most suitable model

---

## ⚙️ Methodology

### 📥 Data Acquisition

Two main sources were used to gather the dataset:

1. **Web scraping** from Zap Imóveis, collecting structured property attributes and price data. The scraping process was parallelized using threads for efficiency.
2. **API from Data.Rio** (Rio de Janeiro’s city government), used to enrich the dataset with contextual information like:
   - Favela boundaries
   - Nearby hospitals
   - Schools
   - Metro stations

### 🧹 Data Preprocessing

- **Geocoding**: Converted addresses into geographic coordinates (latitude, longitude)
- **Feature enrichment**: Added contextual features (infrastructure, proximity to services)
- **Duplicate and missing value removal**
- **Normalization** of numerical data
- **One-Hot Encoding** for categorical variables
- **Outlier detection and removal**

### 🤖 Model Training and Optimization

Algorithms evaluated:

- Linear Regression
- Ridge Regression
- Random Forest Regressor
- XGBoost Regressor
- Deep Neural Networks (Keras)

Techniques used:

- **Grid Search** for hyperparameter tuning
- **Cross-Validation** to reduce bias and ensure model generalizability

### 📏 Evaluation Metrics

- **R² (Coefficient of Determination)**
- **MAPE (Mean Absolute Percentage Error)**
- **MAE (Mean Absolute Error)**
- **RMSE (Root Mean Squared Error)**

---

## 📊 Dataset Summary

### Raw Data Collected

- **Rent**: 10,064 listings
- **Sale**: 8,878 listings

### After Cleaning and Preprocessing

- **Rent**: 1,139 records
- **Sale**: 518 records

---

## 📈 Results

### 🏠 Rent Price Prediction

| Model                   | R² Score | MAPE |
|-------------------------|----------|------|
| Random Forest Regressor | 0.74     | 36%  |
| XGBoost Regressor       | 0.76     | 35%  |
| Neural Network (Keras)  | **0.78** | **33%** |

---

### 🏡 Sale Price Prediction

| Model                   | R² Score | MAPE |
|-------------------------|----------|------|
| Random Forest Regressor | 0.77     | 34%  |
| XGBoost Regressor       | 0.79     | 33%  |
| Neural Network (Keras)  | **0.81** | **31%** |

Over **2,295 model variations** were generated during the tuning process using grid search, confirming the robustness of the final model choices.

---

## ✅ Conclusion

While **neural networks** delivered the best overall metrics, other aspects must also be considered:

- Evaluation metrics
- Interpretability
- Computational cost
- Consistency in training performance

In this case, the neural network outperformed the other models in predictive power but at a **higher computational cost**. Tree-based models like Random Forest and XGBoost showed **greater consistency** and may be preferable in real-world production environments where **efficiency** and **interpretability** are also critical.

---

## 🚀 Future Improvements

- Deploy the solution as a web or mobile platform to assist users in identifying properties with the best cost-benefit ratio
- Integrate geospatial features from external APIs (e.g., walkability scores, public transport access)
- Explore **Explainable AI (XAI)** techniques to increase transparency in complex models

---

## 🛠️ Technologies Used

- **Python**
- **Pandas**, **NumPy**, **Seaborn**, **Matplotlib**
- **Scikit-learn**, **XGBoost**, **Keras**, **TensorFlow**
- **BeautifulSoup**, **Requests** (Web Scraping)
