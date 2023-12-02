
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
from PIL import Image
import datetime


img = Image.open('tondino3.png')
image = Image.open('logo.bettershop.png')

st.set_page_config(
        layout="wide",
        page_title='Market Analysis',
        page_icon=img)

st.image(image, width=400)

st.title("ANALISI DI MERCATO 2 ANNI")
st.markdown("_source.h v.1.0_")

#nascondere dalla pagina la scritta "made with streamlit"
hide_style = """
    <style>
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)



# Accedi al segreto
password_segreta = st.secrets["password"]

# Input per la password
password_input = st.sidebar.text_input("Inserisci la password", type="password")

if password_input:
    if password_input == password_segreta:
        # Create a connection object.
        conn = st.connection("gsheets", type=GSheetsConnection)

        # Chiedi all'utente il nome del foglio
        sheet_name = st.sidebar.text_input("Inserisci il nome del foglio:")

        if sheet_name:
            try:
                # Leggi i dati dal foglio specificato
                data = conn.read(worksheet=sheet_name)

                # Converti in DataFrame di Pandas
                df = pd.DataFrame(data)

                # Rimuovi righe e colonne completamente vuote
                df.dropna(how='all', axis=1, inplace=True)  # Rimuove colonne vuote
                df.dropna(how='all', axis=0, inplace=True)  # Rimuove righe vuote

                colonne_selezionate_fatturato = ['Product', 'ASIN', 'Brand'] + df.columns[51:76].tolist()
                df_selezionato_fatturato = df[colonne_selezionate_fatturato]
                # Inserisci la colonna Somma dopo 'Brand' per fatturato
                df_selezionato_fatturato.insert(3, 'Somma', df_selezionato_fatturato.iloc[:, 3:].sum(axis=1))

                colonne_selezionate_units = ['Product', 'ASIN', 'Brand'] + df.columns[26:51].tolist()
                df_selezionato_units = df[colonne_selezionate_units]
                # Inserisci la colonna Somma dopo 'Brand' per units
                df_selezionato_units.insert(3, 'Somma', df_selezionato_units.iloc[:, 3:].sum(axis=1))

                # Calcola la somma totale di fatturato e units
                total_sum_fatturato = df_selezionato_fatturato['Somma'].sum()
                total_sum_units = df_selezionato_units['Somma'].sum()

                # CSS per centrare e formattare il contenuto nelle colonne
                st.markdown("""
                    <style>
                    .centered {
                        text-align: center;
                    }
                    .metric-title {
                        font-size: 1em;
                        margin-bottom: 5px;
                        font-style: italic;
                    }
                    .metric-value {
                        font-size: 3.5em;  /* Dimensione più grande per i valori */
                        font-weight: normal; /* Rimuove il grassetto */
                    }
                    </style>
                    """, unsafe_allow_html=True)

                # Creazione delle colonne per le metriche
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"<div class='centered'><span class='metric-title'>Totale Fatturato</span><br><span class='metric-value'>€{total_sum_fatturato:,.2f}</span></div>", unsafe_allow_html=True)

                with col2:
                    st.markdown(f"<div class='centered'><span class='metric-title'>Totale Units</span><br><span class='metric-value'>{total_sum_units:,.2f}</span></div>", unsafe_allow_html=True)

                
                # Calcola il numero di valori univoci per ASIN e Brand
                unique_asin_count = df['ASIN'].nunique()
                unique_brand_count = df['Brand'].nunique()

                st.write("\n\n\n\n")

                col3, col4 = st.columns(2)

                with col3:
                    st.markdown(f"<div class='centered'><span class='metric-title'>ASIN</span><br><span class='metric-value'>{unique_asin_count}</span></div>", unsafe_allow_html=True)

                with col4:
                    st.markdown(f"<div class='centered'><span class='metric-title'>Brand</span><br><span class='metric-value'>{unique_brand_count}</span></div>", unsafe_allow_html=True)

                                
                
                st.write("\n\n\n\n")



                st.header("ANALISI FATTURATO")
                with st.expander("VISUALIZZAZIONE FATTURATO"):
                    st.dataframe(df_selezionato_fatturato, use_container_width=True)
                
                
                # Estrai i primi 7 caratteri per le colonne oltre le prime quattro
                colonne_da_modificare = df_selezionato_fatturato.columns[4:]
                colonne_modificate = [col[:7] for col in colonne_da_modificare]
                df_selezionato_fatturato.rename(columns=dict(zip(colonne_da_modificare, colonne_modificate)), inplace=True)

                # Esegui un "unpivot" o "melt"
                data_for_trend = df_selezionato_fatturato.melt(id_vars=['Product', 'ASIN', 'Brand', 'Somma'], 
                                                        var_name='Periodo', 
                                                        value_name='Total')

                # Estrai 'Mese' e 'Anno' dalla colonna 'Periodo'
                data_for_trend[['Mese', 'Anno']] = data_for_trend['Periodo'].str.split("/", expand=True)

                # Visualizza la tabella per confermare le modifiche
                with st.sidebar.expander("Visualizza Tabella Unpivot"):
                    st.dataframe(data_for_trend)



                # Converti 'Periodo' in un oggetto datetime
                data_for_trend['Periodo'] = pd.to_datetime(data_for_trend['Periodo'], format='%m/%Y')

                # Aggrega i dati per 'Brand' e 'Periodo'
                data_aggregated = data_for_trend.groupby(['Brand', 'Periodo'])['Total'].sum().reset_index()

                # Determina i primi 10 brand per fatturato totale
                top_10_brands = data_aggregated.groupby('Brand')['Total'].sum().nlargest(10).index

                # Filtra i dati per includere solo i primi 10 brand
                data_top_10 = data_aggregated[data_aggregated['Brand'].isin(top_10_brands)]

                # Ordina i dati per 'Periodo'
                data_top_10 = data_top_10.sort_values('Periodo')

                # Aggiungi un widget per scegliere il tipo di grafico
                tipo_grafico = st.radio("Seleziona il tipo di visualizzazione:", ['Linea_fatturato', 'Bar_fatturato'])

                # Filtra i dati per i primi 10 brand
                data_top_10 = data_aggregated[data_aggregated['Brand'].isin(top_10_brands)]
                data_top_10 = data_top_10.sort_values('Periodo')

                # Visualizza il grafico in base alla scelta dell'utente
                if tipo_grafico == 'Linea_fatturato':
                    # Grafico a linee
                    fig = px.line(data_top_10, x='Periodo', y='Total', color='Brand', title='Trend dei Top 10 Brand per Mese e Anno')
                    st.plotly_chart(fig, use_container_width=True)
                elif tipo_grafico == 'Bar_fatturato':
                    # Grafico a istogramma con barre affiancate
                    fig = px.bar(data_top_10, x='Periodo', y='Total', color='Brand', title='Distribuzione dei Top 10 Brand per Mese e Anno')
                    st.plotly_chart(fig, use_container_width=True)


                    # Estrai gli anni dai dati
                data_for_trend['Anno'] = pd.to_datetime(data_for_trend['Periodo']).dt.year
                anni_unici = sorted(data_for_trend['Anno'].unique())

                # Aggiungi un filtro per selezionare un Anno per i grafici a barre e a torta
                anno_selezionato = st.radio("Seleziona un Anno (Rev):", options=anni_unici, horizontal=True)

                # Filtra i dati per l'anno selezionato
                data_per_anno = data_for_trend[data_for_trend['Anno'] == anno_selezionato]

                # Aggrega i dati filtrati per Brand
                data_aggregated2_per_anno = data_per_anno.groupby(['Brand'])['Total'].sum().reset_index()

                # Determina i primi 10 brand per fatturato totale
                top_10_brands2_per_anno = data_aggregated2_per_anno.groupby('Brand')['Total'].sum().nlargest(10).index

                # Filtra per i primi 10 brand
                data_top_10_2_per_anno = data_aggregated2_per_anno[data_aggregated2_per_anno['Brand'].isin(top_10_brands2_per_anno)]
                data_top_10_2_per_anno = data_top_10_2_per_anno.sort_values(by='Total', ascending=False)

                # Crea i grafici a barre e a torta per l'anno selezionato
                fig2 = px.histogram(data_top_10_2_per_anno, x='Brand', y='Total', title=f'Total per Brand nel {anno_selezionato}')
                fig3_torta = px.pie(data_top_10_2_per_anno, values='Total', names='Brand', title=f'Percentuale Fatturato per Top 10 Brand nel {anno_selezionato}')

                A, B = st.columns(2)
                with A:
                    st.plotly_chart(fig2, use_container_width=True)
                with B:
                    st.plotly_chart(fig3_torta, use_container_width=True)


            









                
                st.header("ANALISI VOLUMI DI VENDITA")
                with st.expander("VISUALIZZAZIONE UNITS"):
                    st.dataframe(df_selezionato_units, use_container_width=True)

                C,D = st.columns(2)

                # Estrai i primi 7 caratteri per le colonne oltre le prime quattro
                colonne_da_modificare = df_selezionato_units.columns[4:]
                colonne_modificate = [col[:7] for col in colonne_da_modificare]
                df_selezionato_fatturato.rename(columns=dict(zip(colonne_da_modificare, colonne_modificate)), inplace=True)

                # Esegui un "unpivot" o "melt"
                data_for_trend_units = df_selezionato_units.melt(id_vars=['Product', 'ASIN', 'Brand', 'Somma'], 
                                                        var_name='Periodo', 
                                                        value_name='Total')

                # Estrai 'Mese' e 'Anno' dalla colonna 'Periodo'
                data_for_trend_units[['Mese', 'Anno']] = data_for_trend_units['Periodo'].str.split("/", expand=True)

                # Visualizza la tabella per confermare le modifiche
                with st.sidebar.expander("Visualizza Tabella Unpivot"):
                    st.dataframe(data_for_trend_units)



                # Converti 'Periodo' in un oggetto datetime
                data_for_trend_units['Periodo'] = pd.to_datetime(data_for_trend_units['Periodo'], format='%m/%Y')

                # Aggrega i dati per 'Brand' e 'Periodo'
                data_aggregated_units = data_for_trend_units.groupby(['Brand', 'Periodo'])['Total'].sum().reset_index()

                # Determina i primi 10 brand per fatturato totale
                top_10_brands_units = data_aggregated_units.groupby('Brand')['Total'].sum().nlargest(10).index

                # Filtra i dati per includere solo i primi 10 brand
                data_top_10_units = data_aggregated_units[data_aggregated_units['Brand'].isin(top_10_brands)]

                # Ordina i dati per 'Periodo'
                data_top_10_units = data_top_10_units.sort_values('Periodo')

                # Aggiungi un widget per scegliere il tipo di grafico
                tipo_grafico_units = st.radio("Seleziona il tipo di visualizzazione:", ['Linea_units', 'Bar_units'])

                # Filtra i dati per i primi 10 brand
                data_top_10_units = data_aggregated_units[data_aggregated_units['Brand'].isin(top_10_brands_units)]
                data_top_10_units = data_top_10_units.sort_values('Periodo')

                # Visualizza il grafico in base alla scelta dell'utente
                if tipo_grafico_units == 'Linea_units':
                    # Grafico a linee
                    fig_units = px.line(data_top_10_units, x='Periodo', y='Total', color='Brand', title='Trend dei Top 10 Brand per Mese e Anno')
                    st.plotly_chart(fig_units, use_container_width=True)
                elif tipo_grafico_units == 'Bar_units':
                    # Grafico a istogramma con barre affiancate
                    fig_units = px.bar(data_top_10_units, x='Periodo', y='Total', color='Brand', title='Distribuzione dei Top 10 Brand per Mese e Anno')
                    st.plotly_chart(fig_units, use_container_width=True)






                    # Estrai gli anni dai dati
                data_for_trend_units['Anno'] = pd.to_datetime(data_for_trend_units['Periodo']).dt.year
                anni_unici_units = sorted(data_for_trend_units['Anno'].unique())

                # Aggiungi un filtro per selezionare un Anno per i grafici a barre e a torta
                anno_selezionato_units = st.radio("Seleziona un Anno (Units):", options=anni_unici_units, horizontal=True)

                # Filtra i dati per l'anno selezionato
                data_per_anno_units = data_for_trend_units[data_for_trend_units['Anno'] == anno_selezionato_units]

                # Aggrega i dati filtrati per Brand
                data_aggregated2_per_anno_units = data_per_anno_units.groupby(['Brand'])['Total'].sum().reset_index()

                # Determina i primi 10 brand per fatturato totale
                top_10_brands2_per_anno_units = data_aggregated2_per_anno_units.groupby('Brand')['Total'].sum().nlargest(10).index

                # Filtra per i primi 10 brand
                data_top_10_2_per_anno_units = data_aggregated2_per_anno_units[data_aggregated2_per_anno_units['Brand'].isin(top_10_brands2_per_anno_units)]
                data_top_10_2_per_anno_units = data_top_10_2_per_anno_units.sort_values(by='Total', ascending=False)

                # Crea i grafici a barre e a torta per l'anno selezionato
                fig2_units = px.histogram(data_top_10_2_per_anno_units, x='Brand', y='Total', title=f'Total per Brand nel {anno_selezionato_units}')
                fig3_torta_units = px.pie(data_top_10_2_per_anno_units, values='Total', names='Brand', title=f'Percentuale Fatturato per Top 10 Brand nel {anno_selezionato_units}')

                A, B = st.columns(2)
                with A:
                    st.plotly_chart(fig2_units, use_container_width=True)
                with B:
                    st.plotly_chart(fig3_torta_units, use_container_width=True)


                # Selezione delle colonne specifiche per creare una nuova tabella
                colonne_desiderate = ['Product', 'ASIN', 'Brand','Fulfillment', 'Number of sellers', 'Ratings', 
                                    'Review count', 'Images', 'Buy Box', 'Category', 
                                    'Subcategory', 'Variation count']

                # Assicurati che tutte le colonne desiderate siano nel DataFrame
                if all(col in df.columns for col in colonne_desiderate):
                    nuova_tabella = df[colonne_desiderate]
                else:
                    st.error("Alcune colonne desiderate non sono presenti nel DataFrame.")






                # Visualizzazione della nuova tabella
                st.header("DATABASE PRODOTTI")
                st.dataframe(nuova_tabella, use_container_width=True)


                # Unisci i DataFrame sulla colonna 'ASIN'
                data_combinata = pd.merge(df_selezionato_fatturato[['ASIN', 'Somma']], 
                                        nuova_tabella[['ASIN', 'Fulfillment']], 
                                        on='ASIN', 
                                        how='left')
                
                # Crea un grafico a barre
                fig_fulfillment = px.histogram(data_combinata, x='Fulfillment', y='Somma', color='Fulfillment', title='Fatturato per Fulfillment')
                st.plotly_chart(fig_fulfillment, use_container_width=True)
                
                
                # Calcola il conteggio per ciascun valore in "Buy Box"
                conteggio_buy_box = nuova_tabella['Buy Box'].value_counts().reset_index()
                conteggio_buy_box.columns = ['Buy Box', 'Conteggio']

                # Seleziona i primi 20 valori
                top_20_buy_box = conteggio_buy_box.head(20)
                # Grafico a barre per i primi 20 valori in "Buy Box"
                fig_buy_box_top_20 = px.bar(top_20_buy_box, x='Buy Box', y='Conteggio', text='Conteggio', title='Top 20 Valori per Buy Box')
                st.plotly_chart(fig_buy_box_top_20, use_container_width=True)



                E,F = st.columns(2)
                
                
                fig_category = px.histogram(nuova_tabella, x='Category', text_auto=True, title='Conteggio per Categoria')
                
                with E:
                    st.plotly_chart(fig_category, use_container_width=True)
              
                
                fig_subcategory = px.histogram(nuova_tabella, x='Subcategory', text_auto=True, title='Conteggio per Sottocategoria')
                
                with F:
                    st.plotly_chart(fig_subcategory, use_container_width=True)






            except Exception as e:
                st.error(f"Errore: {e}")
        
    else:
        st.error("Password errata. Riprova.")
