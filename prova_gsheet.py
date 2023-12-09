
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
from PIL import Image
import datetime
from streamlit_extras.metric_cards import style_metric_cards 
from wordcloud import WordCloud
import matplotlib.pyplot as plt




img = Image.open('tondino3.png')
image = Image.open('logo.bettershop.png')
image_title =Image.open('bettershop_srls_cover.jpg')

st.set_page_config(
        layout="wide",
        page_title='Market Analysis',
        page_icon=img)

st.sidebar.image(image, width=250)

st.image(image_title,use_column_width=True)

st.title("ANALISI DI MERCATO 2 ANNI")
st.sidebar.markdown("_source.h v.1.0_")

#nascondere dalla pagina la scritta "made with streamlit"
hide_style = """
    <style>
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

# Add custom CSS to hide the GitHub icon
hide_github_icon = """
#GithubIcon {
  visibility: hidden;
}
"""
st.markdown(hide_github_icon, unsafe_allow_html=True)




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

                # Formattazione con il punto come separatore delle migliaia e la virgola per i decimali
                formatted_total_sum_fatturato = "{:,.2f}".format(total_sum_fatturato).replace(",", "X").replace(".", ",").replace("X", ".")
                formatted_total_sum_units = "{:,.0f}".format(total_sum_units).replace(",", "X").replace(".", ",").replace("X", ".")


                # Calcola il numero di valori univoci per ASIN e Brand
                unique_asin_count = df['ASIN'].nunique()
                unique_brand_count = df['Brand'].nunique()

                # Creazione delle colonne per le metriche


                def metrics():
                    from streamlit_extras.metric_cards import style_metric_cards
                    style_metric_cards(background_color="",border_left_color="#f8db0c")
                metrics()

                
                col1, col2 = st.columns(2)
                with col1:    
                    st.metric(label="Totale Fatturato",value=f"{formatted_total_sum_fatturato} €")
                with col2:
                    st.metric(label="Totale Units",value=formatted_total_sum_units)


                st.write("\n\n\n\n")

                col3, col4 = st.columns(2)

                with col3:
                    st.metric(label="ASIN",
                              value=unique_asin_count)

                with col4:
                    st.metric(label="BRAND",
                              value=unique_brand_count)
                                
                
                st.write("\n\n\n\n")


                with st.container(border=True):
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
                    tipo_grafico = st.radio(
                        "Seleziona il tipo di visualizzazione:",
                        ['Linea_fatturato', 'Bar_fatturato', 'KPI_fatturato'],
                        horizontal=True
                    )

                    # Visualizza il grafico in base alla scelta dell'utente
                    if tipo_grafico == 'Linea_fatturato':
                        # Grafico a linee
                        fig = px.line(data_top_10, x='Periodo', y='Total', color='Brand', title='Trend dei Top 10 Brand per Mese e Anno')
                        fig.update_traces(hovertemplate='<br>%{y:,.2f} €')
                        fig.update_layout(hovermode='x unified')
                        st.plotly_chart(fig, use_container_width=True)
                    elif tipo_grafico == 'Bar_fatturato':
                        # Grafico a istogramma con barre affiancate
                        fig = px.bar(data_top_10, x='Periodo', y='Total', color='Brand', title='Distribuzione dei Top 10 Brand per Mese e Anno')
                        fig.update_traces(hovertemplate='%{x}<br>Total: €%{y:,.2f}')
                        st.plotly_chart(fig, use_container_width=True)
                    elif tipo_grafico == 'KPI_fatturato':
                        
                        # Calcolo delle metriche KPI
                    # Estrai l'anno da 'Periodo'
                        data_aggregated['Anno'] = data_aggregated['Periodo'].dt.year

                        # Raggruppa e calcola la somma totale per brand e anno
                        data_aggregated_sum = data_aggregated.groupby(['Brand', 'Anno'])['Total'].sum().reset_index()


                        # Filtra per gli anni 2022 e 2023
                        data_aggregated_filtered = data_aggregated[data_aggregated['Anno'].isin([2022, 2023])]

                        data_aggregated_sum_filtered = data_aggregated_filtered.groupby(['Brand', 'Anno'])['Total'].sum().reset_index()

                        # Calcola il fatturato totale per brand
                        fatturato_per_brand = data_aggregated_sum.groupby('Brand')['Total'].sum()

                        # Filtra per i top 10 brand
                        fatturato_per_brand = fatturato_per_brand[fatturato_per_brand.index.isin(top_10_brands)]
                        
                        # Calcola la variazione percentuale anno su anno per ciascun brand
                        data_aggregated_sum_filtered['Variazione Annuale'] = data_aggregated_sum_filtered.groupby('Brand')['Total'].pct_change()

                        # Calcola la media delle variazioni annuali per ogni brand
                        variazione_media_per_brand = data_aggregated_sum_filtered.groupby('Brand')['Variazione Annuale'].mean()

                        # Visualizzazione delle metriche KPI
                        colA, colB, colC, colD, colE = st.columns(5)
                        colF, colG, colH, colI, colL = st.columns(5)

                        top_10_brands_list = list(fatturato_per_brand.index)

                        # Visualizzazione delle metriche per i top 10 brand
                        for i, brand in enumerate(top_10_brands_list):
                            if i < 5:
                                colonna = [colA, colB, colC, colD, colE][i]
                            else:
                                colonna = [colF, colG, colH, colI, colL][i - 5]

                            fatturato = fatturato_per_brand[brand]
                            variazione = variazione_media_per_brand.get(brand, 0)  # Default a 0 se non presente

                            formatted_fatturato = "{:,.2f}".format(fatturato).replace(",", "X").replace(".", ",").replace("X", ".")


                            colonna.metric(
                                label=brand,
                                value=f"{formatted_fatturato} €",
                                delta=f"{variazione:.2%}" if not pd.isna(variazione) else None
                            )


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
                    fig2 = px.bar(data_top_10_2_per_anno, x='Brand', y='Total', title=f'Total per Brand nel {anno_selezionato}', text='Total')
                    fig2.update_traces(hovertemplate='Brand: %{x}<br>Total: €%{y:,.2f}', texttemplate='%{y:,.2f} €', textposition='outside')

                    fig3_torta = px.pie(data_top_10_2_per_anno, values='Total', names='Brand', title=f'Percentuale Fatturato per Top 10 Brand nel {anno_selezionato}')

                    A, B = st.columns(2)
                    with A:
                        st.plotly_chart(fig2, use_container_width=True)
                    with B:
                        st.plotly_chart(fig3_torta, use_container_width=True)


                









                with st.container(border=True):
                    st.header("ANALISI UNITA' VENDUTE")
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
                    data_top_10_units = data_aggregated_units[data_aggregated_units['Brand'].isin(top_10_brands_units)]

                    # Ordina i dati per 'Periodo'
                    data_top_10_units = data_top_10_units.sort_values('Periodo')

                    # Aggiungi un widget per scegliere il tipo di grafico
                    tipo_grafico_units = st.radio("Seleziona il tipo di visualizzazione:", ['Linea_units', 'Bar_units','KPI_units'], horizontal=True)

                    # Filtra i dati per i primi 10 brand
                    data_top_10_units = data_top_10_units.sort_values('Periodo')

                    # Visualizza il grafico in base alla scelta dell'utente
                    if tipo_grafico_units == 'Linea_units':
                        # Grafico a linee
                        fig_units = px.line(data_top_10_units, x='Periodo', y='Total', color='Brand', title='Trend dei Top 10 Brand per Mese e Anno')
                        fig_units.update_layout(hovermode='x unified')
                        fig_units.update_traces(hovertemplate='%{y}')
                        st.plotly_chart(fig_units, use_container_width=True)
                    elif tipo_grafico_units == 'Bar_units':
                        # Grafico a istogramma con barre affiancate
                        fig_units = px.bar(data_top_10_units, x='Periodo', y='Total', color='Brand', title='Distribuzione dei Top 10 Brand per Mese e Anno')
                        st.plotly_chart(fig_units, use_container_width=True)
                    elif tipo_grafico_units == 'KPI_units':
                        
                        # Calcolo delle metriche KPI
                    # Estrai l'anno da 'Periodo'
                        data_aggregated_units['Anno'] = data_aggregated_units['Periodo'].dt.year

                        # Raggruppa e calcola la somma totale per brand e anno
                        data_aggregated_sum_units = data_aggregated_units.groupby(['Brand', 'Anno'])['Total'].sum().reset_index()

                        # Filtra per gli anni 2022 e 2023
                        data_aggregated_filtered_units = data_aggregated_units[data_aggregated_units['Anno'].isin([2022, 2023])]

                        data_aggregated_sum_filtered_units = data_aggregated_filtered_units.groupby(['Brand', 'Anno'])['Total'].sum().reset_index()

                        # Calcola il fatturato totale per brand
                        quantità_per_brand_units = data_aggregated_sum_units.groupby('Brand')['Total'].sum()

                        # Filtra per i top 10 brand
                        quantità_per_brand_units = quantità_per_brand_units[quantità_per_brand_units.index.isin(top_10_brands_units)]

                        # Calcola la variazione percentuale anno su anno per ciascun brand
                        data_aggregated_sum_filtered_units['Variazione Annuale Units'] = data_aggregated_sum_filtered_units.groupby('Brand')['Total'].pct_change()

                        # Calcola la media delle variazioni annuali per ogni brand
                        variazione_media_per_brand_units = data_aggregated_sum_filtered_units.groupby('Brand')['Variazione Annuale Units'].mean()

                        # Visualizzazione delle metriche KPI
                        colM, colN, colO, colP, colQ = st.columns(5)
                        colR, colS, colT, colU, colV = st.columns(5)

                        top_10_brands_list_units = list(quantità_per_brand_units.index)

                        # Visualizzazione delle metriche per i top 10 brand
                        for i, brand_units in enumerate(top_10_brands_list_units):
                            if i < 5:
                                colonna_units = [colM, colN, colO, colP, colQ][i]
                            else:
                                colonna_units = [colR, colS, colT, colU, colV][i - 5]

                            quantità_units = quantità_per_brand_units[brand_units]
                            variazione_units = variazione_media_per_brand_units.get(brand_units, 0)  # Default a 0 se non presente

                            formatted_quantità_units = "{:,.0f}".format(quantità_units).replace(",", "X").replace(".", ",").replace("X", ".")

                            colonna_units.metric(
                                label=brand_units,
                                value=f"{formatted_quantità_units}",
                                delta=f"{variazione_units:.2%}" if not pd.isna(variazione_units) else None
                            )





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
                    fig2_units = px.bar(data_top_10_2_per_anno_units, x='Brand', y='Total', title=f'Total per Brand nel {anno_selezionato_units}', text='Total')
                    fig2_units.update_traces(hovertemplate='Brand: %{x}<br>Total: %{y}', texttemplate='%{y}', textposition='outside')
                    fig3_torta_units = px.pie(data_top_10_2_per_anno_units, values='Total', names='Brand', title=f'Percentuale Unità venduta per Top 10 Brand nel {anno_selezionato_units}')

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



                #GRAFICO PER FARE ASP PER BRAND

                with st.container(border=True):
                    st.header("ANALISI AVERAGE SELLING PRICE")

                # Aggregazione dei dati
                    total_per_brand_fatturato = data_for_trend.groupby(['Brand','Anno'])['Total'].sum().reset_index()
                    total_per_brand_units = data_for_trend_units.groupby(['Brand', 'Anno'])['Total'].sum().reset_index()

                    # Merge delle tabelle
                    combined_data = pd.merge(total_per_brand_fatturato, total_per_brand_units, on=['Brand', 'Anno'], suffixes=('_fatturato', '_units'))

                    # Calcolo dell'ASP
                    combined_data['ASP'] = combined_data['Total_fatturato'] / combined_data['Total_units']

                    media_asp_totale = round(combined_data['ASP'].mean(),2)

                    col5,col6,col7,col8,col9,col10=st.columns(6)

                    with col5:
                        st.metric(label="Total Market ASP", value=f"{media_asp_totale} €")



                    # Filtro per anno
                    anni_unici_combinato = sorted(combined_data['Anno'].unique())
                    anno_selezionato_combinato = st.radio("Seleziona un Anno (ASP):", options=anni_unici_combinato, horizontal=True)

                    # Filtrare i dati in base all'anno selezionato
                    combined_data_filtered = combined_data[combined_data['Anno'] == anno_selezionato_combinato]

                    # Determina i primi 10 brand per fatturato totale nell'anno selezionato
                    top_10_brands = combined_data_filtered.nlargest(10, 'Total_fatturato')

                    # Creazione di un grafico a barre per il fatturato
                    bar = go.Bar(
                        x=top_10_brands['Brand'], 
                        y=top_10_brands['Total_fatturato'], 
                        name='Fatturato Totale', 
                        yaxis='y', 
                        offsetgroup=1,
                        text=top_10_brands['Total_fatturato'],
                        texttemplate='%{text:,.2f} €',
                        textposition='outside'
                    )

                    # Creazione di un grafico a linee per l'ASP
                    line = go.Scatter(
                        x=top_10_brands['Brand'], 
                        y=top_10_brands['ASP'], 
                        name='ASP', 
                        yaxis='y2', 
                        line=dict(color='red'), 
                        mode='lines+markers',
                        hovertemplate='Brand: %{x}<br>ASP: %{y:.2f} €'
                    )

                    # Impostazioni del layout, inclusa l'asse Y secondaria
                    layout = go.Layout(
                        title='Fatturato Totale e ASP dei Top 10 Brand',
                        yaxis=dict(title='Fatturato Totale'),
                        yaxis2=dict(title='ASP', overlaying='y', side='right'),
                        xaxis=dict(title='Brand'),
                        barmode='group')



                    # Combinazione dei grafici
                    fig_combinato = go.Figure(data=[bar, line], layout=layout)

                    # Visualizzazione del grafico
                    st.plotly_chart(fig_combinato, use_container_width=True)




                with st.container(border=True):
                    # Visualizzazione della nuova tabella
                    st.header("DATABASE PRODOTTI")
                    with st.expander("Visualizza database"):
                        st.dataframe(nuova_tabella, use_container_width=True)


                    # Assicurati che top_10_brands contenga solo i nomi dei brand
                    top_10_brand_names = top_10_brands['Brand'].tolist()

                    # Filtra nuova_tabella per i brand in top_10_brand_names
                    filtered_nuova_tabella = nuova_tabella[nuova_tabella['Brand'].isin(top_10_brand_names)]

                    # Conteggio delle occorrenze di Brand in nuova_tabella
                    conteggio_brand_nuova_tabella = filtered_nuova_tabella['Brand'].value_counts().reset_index()
                    conteggio_brand_nuova_tabella.columns = ['Brand', 'Conteggio']

                    # Seleziona i primi 10 Brand
                    top_10_brands_conteggio = conteggio_brand_nuova_tabella.head(10)

                    # Crea un grafico a barre
                    fig_conteggio_brand = px.bar(top_10_brands_conteggio, x='Brand', y='Conteggio', title='Conteggio prodotti dei Top 10 Brand per Fatturato', text_auto=True)

                    # Visualizzazione del grafico
                    st.plotly_chart(fig_conteggio_brand, use_container_width=True)



                    # Funzione per convertire in numerico, gestendo errori
                    def safe_convert_to_numeric(series):
                        return pd.to_numeric(series, errors='coerce')

                    # Converti le colonne in valori numerici
                    filtered_nuova_tabella['Ratings'] = safe_convert_to_numeric(filtered_nuova_tabella['Ratings'])
                    filtered_nuova_tabella['Review count'] = safe_convert_to_numeric(filtered_nuova_tabella['Review count'])
                    filtered_nuova_tabella['Images'] = safe_convert_to_numeric(filtered_nuova_tabella['Images'])
                    filtered_nuova_tabella['Variation count'] = safe_convert_to_numeric(filtered_nuova_tabella['Variation count'])

                    # Calcolo delle medie
                    media_ratings = filtered_nuova_tabella.groupby('Brand')['Ratings'].mean().reset_index()
                    media_review_count = filtered_nuova_tabella.groupby('Brand')['Review count'].mean().reset_index()
                    media_images = filtered_nuova_tabella.groupby('Brand')['Images'].mean().reset_index()
                    media_variation_count = filtered_nuova_tabella.groupby('Brand')['Variation count'].mean().reset_index()

                    # Creazione dei grafici a barre orizzontali con tooltip e valori arrotondati
                    fig_ratings = px.bar(media_ratings, y='Brand', x='Ratings', title='Media Ratings per i Top 10 Brand', orientation='h', labels={'Brand': ''}, text='Ratings')
                    fig_ratings.update_traces(hovertemplate='Brand: %{y}<br>Ratings: %{x:.2f}', texttemplate='%{x:.2f}', textposition='outside')

                    fig_review_count = px.bar(media_review_count, y='Brand', x='Review count', title='Media Review Count per i Top 10 Brand', orientation='h', labels={'Brand': ''}, text='Review count')
                    fig_review_count.update_traces(hovertemplate='Brand: %{y}<br>Review Count: %{x:.2f}', texttemplate='%{x:.2f}', textposition='outside')

                    fig_images = px.bar(media_images, y='Brand', x='Images', title='Media Images per i Top 10 Brand', orientation='h', labels={'Brand': ''}, text='Images')
                    fig_images.update_traces(hovertemplate='Brand: %{y}<br>Images: %{x:.2f}', texttemplate='%{x:.2f}', textposition='outside')

                    fig_variation_count = px.bar(media_variation_count, y='Brand', x='Variation count', title='Media Variation Count per i Top 10 Brand', orientation='h', labels={'Brand': ''}, text='Variation count')
                    fig_variation_count.update_traces(hovertemplate='Brand: %{y}<br>Variation Count: %{x:.2f}', texttemplate='%{x:.2f}', textposition='outside')


                    st.subheader('Media KPIs')
                    # Visualizzazione dei grafici
                    col13, col14, col15, col16 = st.columns(4)
                    with col13:
                        st.plotly_chart(fig_ratings, use_container_width=True)
                    with col14:
                        st.plotly_chart(fig_review_count, use_container_width=True)
                    with col15:
                        st.plotly_chart(fig_images, use_container_width=True)
                    with col16:
                        st.plotly_chart(fig_variation_count, use_container_width=True)





                    # Unisci i DataFrame sulla colonna 'ASIN'
                    data_combinata = pd.merge(df_selezionato_fatturato[['ASIN', 'Somma']], 
                                            nuova_tabella[['ASIN', 'Fulfillment']], 
                                            on='ASIN', 
                                            how='left')
                    
                    # Crea un grafico a barre
                    fig_fulfillment = px.histogram(data_combinata, x='Fulfillment', y='Somma', color='Fulfillment', title='Fatturato per Fulfillment')
                    fig_fulfillment.update_traces(texttemplate='%{y:,.2f} €', textposition='outside')
                    fig_fulfillment.update_traces(hovertemplate='Fulfillment: %{x}<br>Fatturato: €%{y:,.2f}')
                    
                    # Calcolo del conteggio per ogni valore di Fulfillment
                    conteggio_fulfillment = data_combinata['Fulfillment'].value_counts().reset_index()
                    conteggio_fulfillment.columns = ['Fulfillment', 'Conteggio']

                    # Crea un grafico a barre per mostrare il conteggio
                    fig_conteggio_fulfillment = px.bar(conteggio_fulfillment, x='Fulfillment', y='Conteggio',
                                                    title='Conteggio per Fulfillment', 
                                                    labels={'Conteggio': 'Numero di Occorrenze'},text_auto=True)

                    
                    col11, col12 = st.columns(2)
                    with col11:
                        st.plotly_chart(fig_fulfillment, use_container_width=True)
                    with col12:
                        st.plotly_chart(fig_conteggio_fulfillment, use_container_width=True)
                



                    E,F = st.columns(2)
                    
                    
                    fig_category = px.histogram(nuova_tabella, x='Category', text_auto=True, title='Conteggio per Categoria')
                    
                    with E:
                        st.plotly_chart(fig_category, use_container_width=True)
                
                    
                    fig_subcategory = px.histogram(nuova_tabella, x='Subcategory', text_auto=True, title='Conteggio per Sottocategoria')
                    
                    with F:
                        st.plotly_chart(fig_subcategory, use_container_width=True)
                
                
                with st.container(border=True):
                    st.subheader('ANALISI CLOUD KEYWORDS')
                    # Widget per la selezione del filtro
                    opzione_wc = st.radio("Genera Nuvola per:", ["Tutti i Prodotti", "Solo Top 10 Brand per Fatturato"],horizontal=True)

                    def filter_short_words(text):
                        return ' '.join([word for word in text.split() if len(word) >= 3])

                    if opzione_wc == "Solo Top 10 Brand per Fatturato":
                        # Estrai i nomi dei top 10 brand
                        top_10_brand_names = top_10_brands['Brand'].tolist()

                        # Widget per selezionare un brand dai top 10
                        brand_selezionato = st.selectbox("Seleziona un Brand:", top_10_brand_names)

                        # Filtra nuova_tabella per il brand selezionato
                        filtered_nuova_tabella = nuova_tabella[nuova_tabella['Brand'] == brand_selezionato]
                        
                        # Genera il testo per la word cloud
                        text = " ".join(descrizione for descrizione in filtered_nuova_tabella.Product if isinstance(descrizione, str))
                        # Filtra le parole corte
                        text = filter_short_words(text)
                    else:
                        # Utilizza tutti i prodotti in nuova_tabella
                        text = " ".join(descrizione for descrizione in nuova_tabella.Product if isinstance(descrizione, str))
                        # Filtra le parole corte
                        text = filter_short_words(text)

                    # Creazione della Word Cloud
                    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)

                    # Visualizza la Word Cloud usando Matplotlib
                    plt.figure(figsize=(10, 5))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis("off")
                    plt.show()

                    # Mostra la word cloud in Streamlit
                    st.pyplot(plt)   








            except Exception as e:
                st.error(f"Errore: {e}")
        
    else:
        st.error("Password errata. Riprova.")
