import streamlit as st
from neo4j import GraphDatabase, Result
import folium
from streamlit_folium import folium_static
from branca.element import IFrame


URI = st.secrets["db_uri"]
AUTH = (st.secrets["db_username"], st.secrets["db_password"])
database = st.secrets["db_name"]

# Create a Streamlit app
st.set_page_config(layout='wide')

st.title("U.S. Flu Vaccine Provider Search")
st.text("""Enter a zipcode at the left.  Click any map marker to reveal full provider details.""")

# Sidebar for user input
st.sidebar.header("Search Parameters")
zip_code = st.sidebar.text_input("Enter a 5-digit zip code:", max_chars=5, placeholder="55111")
radius = st.sidebar.radio("Select Search Radius (miles):", [5, 15, 25])
submitted = st.sidebar.button("Submit")

if submitted:
    with GraphDatabase.driver(URI, auth=AUTH, database=database) as driver: 
        result = driver.execute_query(
            query_ = """MATCH (z:Zipcode {zipcode: $zipcode})
                        WITH z
                        MATCH (p:Provider) WHERE point.distance(z.location, p.location) < (1609 * $radius)
                        RETURN p.name, p.address, p.location.x, p.location.y, p.phone,
                        p.sunday, p.monday, p.tuesday, p.wednesday, p.thursday, p.friday, p.saturday,
                        p.notes, p.category, p.stock, p.url, p.prescreenURL, p.dateUpdated, p.insuranceAccepted, p.walkinsAccepted""",
                zipcode=str(zip_code),
                radius=radius,
                result_transformer_= Result.to_df
         )
        
        zip_code_location = driver.execute_query(
            query_ = """MATCH (z:Zipcode {zipcode: $zipcode})
                        RETURN z.location.x, z.location.y""",
                zipcode=str(zip_code),
                result_transformer_= Result.to_df
         )

    # Create a Folium map
    zoom_dict = {5: 11, 15: 10, 25: 9}
    zoom_start = zoom_dict[radius]
    m = folium.Map(location=[zip_code_location.iloc[0, 1], zip_code_location.iloc[0, 0]], zoom_start=zoom_start)

    st.text(f"--- {len(result)} results ---")

    for location in result.iterrows():

        url = location[1]["p.url"] if location[1]["p.url"] else ""
        prescreen_url = location[1]["p.prescreenURL"] if location[1]["p.prescreenURL"] else ""

        html = f"""
                <font face="Arial">
                   <b> {location[1]["p.name"]}</b>
                   <p style="font-size:12;">{location[1]["p.phone"]}<br>
                   {location[1]["p.address"]}</p>

                    <table style="font-size:11;">

                        <tr>
                            <td>Sun</td>
                            <td>{location[1]["p.sunday"]}</td>
                        </tr>

                        <tr>
                            <td>Mon</td>
                            <td>{location[1]["p.monday"]}</td>
                        </tr>

                        <tr>
                            <td>Tue</td>
                            <td>{location[1]["p.tuesday"]}</td>
                        </tr>

                        <tr>
                            <td>Wed</td>
                            <td>{location[1]["p.wednesday"]}</td>
                        </tr>

                        <tr>
                            <td>Thu</td>
                            <td>{location[1]["p.thursday"]}</td>
                        </tr>

                        <tr>
                            <td>Fri</td>
                            <td>{location[1]["p.friday"]}</td>
                        </tr>

                        <tr>
                            <td>Sat</td>
                            <td>{location[1]["p.saturday"]}</td>
                        </tr>          

                    </table>

                    <p style="font-size:13;">Notes: {location[1]["p.notes"]}</p>
                    <p style="font-size:13;">{location[1]["p.stock"]} in stock as of {location[1]["p.dateUpdated"]}.</p>
                    <p style="font-size:13;">Walk-ins accepted? {location[1]["p.walkinsAccepted"]}<br>
                                             Insurance accepted? {location[1]["p.insuranceAccepted"]}</p>
                    <p style="font-size:13;"><a href={url}>{url}</a><br>
                                             <a href={prescreen_url}>{prescreen_url}</a></p>
                </font>
                   """
        iframe = IFrame(html=html, width=500, height=400)
        popup = folium.Popup(iframe, max_width=500)     
        folium.Marker(
            location=[location[1]["p.location.y"], location[1]["p.location.x"]],
            popup=popup,
            tooltip=location[1]["p.name"]
        ).add_to(m)

    st_data = folium_static(m, width=900)
else:
    with GraphDatabase.driver(URI, auth=AUTH, database=database) as driver: 
        result = driver.execute_query(
            query_ = """MATCH (p:Provider)
                        RETURN COUNT(*)""",
                result_transformer_= Result.to_df
         )

    st.text(f"--- {result.iloc[0, 0]} total providers ---")

    m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
    st_data = folium_static(m, width=900)

st.markdown("""
            DISCLAIMER: This tool is for informational purposes only and is based on data provided by the [Centers for Disease Control](https://data.cdc.gov/Flu-Vaccinations/Vaccines-gov-Flu-vaccinating-provider-locations/bugr-bbfr).
            Author makes no claim as to the accuracy of this data.  For authoritative information, please visit provider sites directly.
            """)


