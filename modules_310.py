import re
import itertools
import numpy as np
import pandas as pd
import seaborn as sns
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import make_scorer, mean_absolute_error, mean_squared_error, r2_score
from sklearn.inspection import permutation_importance
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from joblib import Parallel, delayed
import tensorflow as tf
from tensorflow.keras import metrics
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, Input, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.regularizers import l2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense


# Função para criar e treinar o modelo de rede neural
def criar_rede_neural(input_shape, learning_rate=0.001, hidden_layers=2, neurons=64, dropout_rate=0.2, activation='relu', 
                      output_activation='linear', optimizer='adam', l2_reg=0.01):
    
    # Verificar parâmetros
    if hidden_layers < 1:
        raise ValueError("O número de camadas ocultas deve ser pelo menos 1.")
    if neurons < 1:
        raise ValueError("O número de neurônios deve ser pelo menos 1.")
    if not 0 <= dropout_rate < 1:
        raise ValueError("A taxa de dropout deve estar entre 0 e 1.")

    model = Sequential()
    model.add(Input(shape=(input_shape,)))
    model.add(Dense(neurons, activation=activation, kernel_regularizer=l2(l2_reg)))

    # Adicionar camadas ocultas
    for _ in range(hidden_layers - 1):
        model.add(Dense(neurons, activation=activation, kernel_regularizer=l2(l2_reg)))
        model.add(Dropout(dropout_rate))

    # Camada de saída (1 neurônio para regressão)
    model.add(Dense(1, activation='linear'))

    # Escolher otimizador
    if optimizer.lower() == 'adam':
        optimizer = Adam(learning_rate=learning_rate)
    elif optimizer.lower() == 'sgd':
        optimizer = SGD(learning_rate=learning_rate)
    else:
        raise ValueError("Otimizador não suportado. Use 'adam' ou 'sgd'.")

    # Compilar o modelo
    model.compile(
        optimizer=optimizer, 
        loss='mse', 
        metrics=['mae'])
    
    return model

def testar_modelo(lr, hidden_layers, neurons, activation, dropout, X_train, y_train, X_test, y_test):

    def learning_rate_scheduler(epoch, lr):
        return float(lr * tf.math.exp(-0.09))

    # Criar o modelo
    model = criar_rede_neural(
        input_shape=X_train.shape[1], 
        learning_rate=lr, 
        hidden_layers=hidden_layers, 
        neurons=neurons, 
        dropout_rate=dropout, 
        activation=activation
    )

    # Treinar o modelo
    model.fit(X_train, y_train, epochs=100, batch_size=32, verbose=0, callbacks=[tf.keras.callbacks.LearningRateScheduler(learning_rate_scheduler)])
    
    # Fazer previsões
    y_pred = model.predict(X_test)
    
    # Calcular métricas
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # Retornar resultados e o modelo
    return mae, rmse, r2, model

def testar_varios_modelos_paralelo(X_train, X_test, y_train, y_test):
    
    # Parâmetros para testar
    learning_rates = [0.001, 0.01, 0.1]
    hidden_layer_options = [1, 2, 3]
    neurons_options = [32, 64, 128]
    activation_functions = ['relu', 'tanh', 'sigmoid']
    dropout_rates = [0.2, 0.3, 0.5]
    
    param_combinations = list(itertools.product(learning_rates, hidden_layer_options, neurons_options, activation_functions, dropout_rates))
        
    # Executar os testes em paralelo
    results = Parallel(n_jobs=-1)(
        delayed(testar_modelo)(lr, hidden_layers, neurons, activation, dropout, X_train, y_train, X_test, y_test)
        for lr, hidden_layers, neurons, activation, dropout in tqdm(param_combinations, desc="Testando combinações")
    )
    
    # Identificar o melhor modelo
    best_score = float('inf')
    best_model = None
    
    for mae, rmse, r2, model in results:
        print(f"MAE: {mae:.4f} | RMSE: {rmse:.4f} | R²: {r2:.4f}")
        if mae < best_score:
            best_score = mae
            best_model = model
    
    return best_model, best_score


