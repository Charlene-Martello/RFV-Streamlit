import numpy as np 
import pandas as pd
import streamlit as st

from datetime import datetime
from PIL import Image
from io import BytesIO

#Set no tema do seaborn para melhorar o visual dos plots
custom_params = {"axes.spines.right": False, "axes.spines.top": False}

@st.cache_resource
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

#Função para converter o df para excel
@st.cache_resource
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

### Criando os Segmentos
def recencia_class(x, r, q_dict):
    """Classifica como melhor o menor quartil 
       x = valor da linha,
       r = recencia,
       q_dict = quartil dicionario   
    """
    if x <= q_dict[r][0.25]:
        return 'A'
    elif x <= q_dict[r][0.50]:
        return 'B'
    elif x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'


def freq_val_class(x, fv, q_dict):
    """Classifica como melhor o maior quartil 
       x = valor da linha,
       fv = frequencia ou valor,
       q_dict = quartil dicionario   
    """
    if x <= q_dict[fv][0.25]:
        return 'D'
    elif x <= q_dict[fv][0.50]:
        return 'C'
    elif x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'

#Função principal da aplicação
def main():
    #config inicial da página de aplicação
    st.set_page_config(
    page_title='Telemarketing Analysis',
    # page_icon='telemarketing_icon.png',  # Descomente esta linha e forneça o ícone apropriado se necessário
    layout="wide",
    initial_sidebar_state='expanded'
)

    #titulo principal da aplicação
    st.write('## RFV')
    st.write ("""
    RFV significa Recência, Frequência e Valor e é utilizado para segmentação
    de clientes baseado no comportamento de compra dos clientes e agrupa eles em 
    clusters parecidos. Utilizando esse tipo de agrupamento podemos realizar
    ações de marketing e CRM melhores direcionadas, ajudando assim na personalização
    do conteúdo e até a retenção de clientes.
              
    Para cada cliente é preciso calcular cada uma das componentes abaixo:
              
    - Recência (R): Quantidade de dias desde a última compra.
    - Frequência (F): Quantidade total de compras no período.
    - Valor (V): Total de dinheiro gasto nas compras no período.
              
    E é isso que iremos fazer abaixo.
    """)
    st.markdown ("---")

    #Apresenta a imagem na barra lateral da aplicação
    #image = Image.open("Bank-Branding.jpg")
    #st.sidebar.image(Image)

    #Botão para carregar arquivo na aplicação
    st.sidebar.write("## Suba o arquivo")
    data_file_1 = st.sidebar.file_uploader("Bank marketing data", type = ['csv', 'xlsx'])

    #Vefirica se há conteúdo carregado na aplicação
    if (data_file_1 is not None):
        df_compras = pd.read_csv(data_file_1, infer_datetime_format=True, parse_dates=['DiaCompra'])

        st.write('## Recência (R)')

        dia_atual = df_compras['DiaCompra'].max()
        st.write('Dia máximo na base de dados: ', dia_atual)

        st.write('Quantos dias faz que o cliente fez sua última compra?')

        
        df_recencia = df_compras.groupby(by='ID_cliente', as_index=False)['DiaCompra'].max()
        df_recencia.columns = ['ID_cliente', 'DiaUltimaCompra']
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual - x).days)
        st.write(df_recencia.head())

        df_recencia.drop('DiaUltimaCompra', axis=1, inplace=True)

        st.write('## Frequência (F)')
        st.write('Quantas vezes cada cliente comprou com a gente?')
        df_frequencia = df_compras[['ID_cliente', 'CodigoCompra']].groupby('ID_cliente').count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']
        st.write(df_frequencia.head())

        st.write('## Valor (V)')
        st.write('Quanto cada cliente gastou no período analisado?')
        df_valor = df_compras[['ID_cliente', 'ValorTotal']].groupby('ID_cliente').sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']
        st.write(df_valor.head())

        st.write('## Tabela RFV final')
        df_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
        df_RFV = df_RF.merge(df_valor, on='ID_cliente')
        df_RFV.set_index('ID_cliente', inplace=True)
        st.write(df_RFV.head())

        st.write('## Segmentação de Clientes utilizando o RFV')
        st.write("Um jeito de segmentar os clientes é criando quartis para cada componente do RFV, sendo que o melhor quartil é chamado de 'A', o segundo melhor quartil de 'B', o terceiro melhor de 'C' e o pior de 'D'. O melhor e o pior depende da componente. Por exemplo, quanto menor a recência melhor é o cliente (pois ele comprou com a gente tem pouco tempo) logo o menor quartil seria classificado como 'A', já pra componente frêquencia a lógica se inverte, ou seja, quanto maior a frêquencia do cliente comprar com a gente, melhor ele/a é, logo, o maior quartil recebe a letra 'A'.")
        st.write('Se a gente tiver interessado em mais ou menos classes, basta a gente aumentar ou diminuir o número de quantils pra cada componente.')
        
        st.write('#### Quartis para o RFV:')
        quartis = df_RFV.quantile(q=[0.25, 0.5, 0.75])
        st.write(quartis)

        st.write('#### Tabela após a criação dos grupos:')
        df_RFV['R_quartil'] = df_RFV['Recencia'].apply(recencia_class,
                                                args=('Recencia', quartis))
        df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(freq_val_class,
                                                  args=('Frequencia', quartis))
        df_RFV['V_quartil'] = df_RFV['Valor'].apply(freq_val_class,
                                             args=('Valor', quartis))
        df_RFV['RFV_Score'] = (df_RFV.R_quartil 
                            + df_RFV.F_quartil 
                            + df_RFV.V_quartil)
        st.write(df_RFV.head())

        st.write('#### Quantidade de clientes por grupo:')
        st.write(df_RFV['RFV_Score'].value_counts())

        st.write('#### Clientes com menor recência, maior frequência e maior gasto:')
        st.write(df_RFV[df_RFV['RFV_Score'] == 'AAA'].sort_values('Valor', ascending=False).head(10))

        st.write('### Ações de Marketing/CRM:')
        dict_acoes = {'AAA':'Enviar cupons de desconto, Pedir para indicar nosso produto pra algum amigo, Ao lançar um novo produto enviar amostras grátis pra esses.',
        'DDD': 'Churn! clientes que gastaram bem pouco e fizeram poucas compras, fazer nada',
        'DAA':'Churn! clientes que gastaram bastante e fizeram muitas compras, enviar cupons de desconto para tentar recuperar',
        'CAA':'Churn! clientes que gastaram bastante e fizeram muitas compras, enviar cupons de desconto para tentar recuperar'
        }

        df_RFV['acoes de marketing/crm'] = df_RFV['RFV_Score'].map(dict_acoes)
        st.write(df_RFV.head())


        #df_RFV_to_excel('RFV_.xlsx')
        df_xlsx = to_excel(df_RFV)
        st.download_button(label= 'Download',
                           data=df_xlsx ,
                           file_name= 'RFV_.xlsx')
        
        st.write('Quantidade de clientes por tipo de ação')
        st.write(df_RFV['acoes de marketing/crm'].value_counts(dropna=False))
    
if __name__== '__main__':
    main()