"""
EPDV Web Demo - EUNIS Proxy Distribution Viewer
Author: Mohamed Z. Hatim, Wageningen University & Research
Developed in collaboration with WENR Team Earth Observation & Environmental Informatics

A web-based demonstration of the EPDV QGIS plugin for EUNIS habitat prediction.
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, List, Tuple
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="EPDV - EUNIS Habitat Predictor",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SAMPLE DATA - EUNIS HABITAT TYPES AND INDICATOR SPECIES
# In the full plugin, this comes from PostgreSQL (98M+ records)
# ============================================================================

# Sample EUNIS Habitat Types (subset of 200+ types)
EUNIS_HABITATS = {
    "N10": {
        "name": "Atlantic, Baltic and Arctic sand beach",
        "description": "Sandy beaches of the Atlantic, Baltic and Arctic coasts, including strandlines.",
        "level": 2
    },
    "N11": {
        "name": "Atlantic and Baltic shingle beach",
        "description": "Shingle and gravel beaches of Atlantic and Baltic coasts.",
        "level": 2
    },
    "MA1": {
        "name": "Littoral rock",
        "description": "Rock in the littoral zone (intertidal), including rockpools.",
        "level": 2
    },
    "MA22": {
        "name": "Littoral salt marsh",
        "description": "Salt marshes in the intertidal zone along coasts.",
        "level": 2
    },
    "MA222": {
        "name": "Atlantic upper saltmarsh",
        "description": "Upper zones of Atlantic coastal salt marshes with characteristic halophytic vegetation.",
        "level": 3
    },
    "MA223": {
        "name": "Atlantic lower saltmarsh",
        "description": "Lower zones of Atlantic salt marshes regularly flooded by tides.",
        "level": 3
    },
    "Q11": {
        "name": "Raised bog",
        "description": "Acidic, oligotrophic peat bogs raised above groundwater level.",
        "level": 2
    },
    "Q12": {
        "name": "Blanket bog",
        "description": "Peatlands covering large areas in oceanic climates.",
        "level": 2
    },
    "Q21": {
        "name": "Valley mire",
        "description": "Peatlands in valleys fed by nutrient-poor groundwater.",
        "level": 2
    },
    "Q4": {
        "name": "Base-rich fen",
        "description": "Fens with calcareous or base-rich groundwater influence.",
        "level": 2
    },
    "Q41": {
        "name": "Alkaline, calcareous fen",
        "description": "Fens developing on calcareous substrates with alkaline water.",
        "level": 2
    },
    "Q51": {
        "name": "Tall-sedge bed",
        "description": "Wetlands dominated by tall Carex species.",
        "level": 2
    },
    "R1A": {
        "name": "Semi-dry perennial calcareous grassland",
        "description": "Species-rich calcareous grasslands on dry, calcium-rich soils.",
        "level": 2
    },
    "R1B": {
        "name": "Heavy-metal grassland",
        "description": "Grasslands on soils with elevated heavy metal concentrations.",
        "level": 2
    },
    "R21": {
        "name": "Mesic permanent pasture",
        "description": "Agriculturally improved permanent pastures on mesic soils.",
        "level": 2
    },
    "R22": {
        "name": "Low and medium altitude hay meadow",
        "description": "Traditional hay meadows at lower elevations.",
        "level": 2
    },
    "R35": {
        "name": "Moist or wet oligotrophic grassland",
        "description": "Nutrient-poor wet grasslands, often species-rich.",
        "level": 2
    },
    "R37": {
        "name": "Moist or wet mesotrophic to eutrophic grassland",
        "description": "Nutrient-rich wet meadows and grasslands.",
        "level": 2
    },
    "S31": {
        "name": "Atlantic wet heath",
        "description": "Wet heathlands in Atlantic climatic regions.",
        "level": 2
    },
    "S41": {
        "name": "Atlantic dry heath",
        "description": "Dry heathlands dominated by Calluna and Erica species.",
        "level": 2
    },
    "S42": {
        "name": "Continental dry heath",
        "description": "Dry heathlands in continental climate zones.",
        "level": 2
    },
    "T11": {
        "name": "Temperate Salix and Populus riparian forest",
        "description": "Softwood floodplain forests with willows and poplars.",
        "level": 2
    },
    "T12": {
        "name": "Temperate Fraxinus-Alnus forest",
        "description": "Wet forests dominated by ash and alder along streams.",
        "level": 2
    },
    "T13": {
        "name": "Temperate hardwood riparian forest",
        "description": "Hardwood forests on floodplains with oak, elm, and ash.",
        "level": 2
    },
    "T17": {
        "name": "Fagus forest on non-acid soil",
        "description": "Beech forests on calcareous or neutral soils.",
        "level": 2
    },
    "T18": {
        "name": "Fagus forest on acid soil",
        "description": "Beech forests on acidic, nutrient-poor soils.",
        "level": 2
    },
    "T1F": {
        "name": "Broadleaved swamp forest on acid peat",
        "description": "Deciduous forests on wet, acidic peat soils.",
        "level": 2
    },
    "T1H": {
        "name": "Temperate and boreal Quercus forest",
        "description": "Oak-dominated forests in temperate regions.",
        "level": 2
    },
    "T3F": {
        "name": "Picea forest on acid soil",
        "description": "Spruce forests on acidic substrates.",
        "level": 2
    },
    "T3G": {
        "name": "Pinus sylvestris forest",
        "description": "Scots pine forests on various substrates.",
        "level": 2
    },
}

# Indicator species for each habitat (Diagnostic, Dominant, Constant with weights)
# In full plugin: 15,119 species-habitat associations from eunis_species_values
INDICATOR_SPECIES = {
    # =========================================================================
    # COASTAL HABITATS
    # =========================================================================
    "N10": {  # Atlantic, Baltic and Arctic sand beach
        "diagnostic": [
            {"species": "Cakile maritima", "weight": 0.95, "common_name": "Sea Rocket"},
            {"species": "Salsola kali", "weight": 0.90, "common_name": "Prickly Saltwort"},
            {"species": "Honckenya peploides", "weight": 0.85, "common_name": "Sea Sandwort"},
            {"species": "Atriplex laciniata", "weight": 0.80, "common_name": "Frosted Orache"},
        ],
        "dominant": [
            {"species": "Elymus farctus", "weight": 0.90, "common_name": "Sand Couch"},
            {"species": "Ammophila arenaria", "weight": 0.85, "common_name": "Marram Grass"},
        ],
        "constant": [
            {"species": "Beta vulgaris subsp. maritima", "weight": 0.70, "common_name": "Sea Beet"},
            {"species": "Crambe maritima", "weight": 0.65, "common_name": "Sea Kale"},
            {"species": "Eryngium maritimum", "weight": 0.60, "common_name": "Sea Holly"},
        ]
    },
    "N11": {  # Atlantic and Baltic shingle beach
        "diagnostic": [
            {"species": "Crambe maritima", "weight": 0.95, "common_name": "Sea Kale"},
            {"species": "Lathyrus japonicus", "weight": 0.90, "common_name": "Sea Pea"},
            {"species": "Glaucium flavum", "weight": 0.85, "common_name": "Yellow Horned-poppy"},
        ],
        "dominant": [
            {"species": "Rumex crispus", "weight": 0.80, "common_name": "Curled Dock"},
            {"species": "Silene uniflora", "weight": 0.75, "common_name": "Sea Campion"},
        ],
        "constant": [
            {"species": "Sedum acre", "weight": 0.70, "common_name": "Biting Stonecrop"},
            {"species": "Honkenya peploides", "weight": 0.65, "common_name": "Sea Sandwort"},
            {"species": "Tripleurospermum maritimum", "weight": 0.60, "common_name": "Sea Mayweed"},
        ]
    },
    "MA1": {  # Littoral rock
        "diagnostic": [
            {"species": "Fucus spiralis", "weight": 0.95, "common_name": "Spiral Wrack"},
            {"species": "Pelvetia canaliculata", "weight": 0.90, "common_name": "Channelled Wrack"},
            {"species": "Fucus vesiculosus", "weight": 0.85, "common_name": "Bladder Wrack"},
        ],
        "dominant": [
            {"species": "Ascophyllum nodosum", "weight": 0.90, "common_name": "Egg Wrack"},
            {"species": "Fucus serratus", "weight": 0.85, "common_name": "Serrated Wrack"},
        ],
        "constant": [
            {"species": "Enteromorpha intestinalis", "weight": 0.70, "common_name": "Gut Weed"},
            {"species": "Ulva lactuca", "weight": 0.65, "common_name": "Sea Lettuce"},
            {"species": "Chondrus crispus", "weight": 0.60, "common_name": "Irish Moss"},
        ]
    },
    "MA22": {  # Littoral salt marsh (general)
        "diagnostic": [
            {"species": "Salicornia europaea", "weight": 0.95, "common_name": "Common Glasswort"},
            {"species": "Suaeda maritima", "weight": 0.90, "common_name": "Annual Sea-blite"},
            {"species": "Spartina anglica", "weight": 0.85, "common_name": "Common Cord-grass"},
        ],
        "dominant": [
            {"species": "Puccinellia maritima", "weight": 0.90, "common_name": "Common Saltmarsh-grass"},
            {"species": "Halimione portulacoides", "weight": 0.85, "common_name": "Sea Purslane"},
        ],
        "constant": [
            {"species": "Aster tripolium", "weight": 0.75, "common_name": "Sea Aster"},
            {"species": "Spergularia media", "weight": 0.70, "common_name": "Greater Sea-spurrey"},
            {"species": "Cochlearia officinalis", "weight": 0.65, "common_name": "Common Scurvygrass"},
        ]
    },
    "MA222": {  # Atlantic upper saltmarsh
        "diagnostic": [
            {"species": "Limonium vulgare", "weight": 0.95, "common_name": "Common Sea Lavender"},
            {"species": "Artemisia maritima", "weight": 0.90, "common_name": "Sea Wormwood"},
            {"species": "Aster tripolium", "weight": 0.85, "common_name": "Sea Aster"},
            {"species": "Triglochin maritimum", "weight": 0.80, "common_name": "Sea Arrowgrass"},
        ],
        "dominant": [
            {"species": "Puccinellia maritima", "weight": 0.90, "common_name": "Common Saltmarsh-grass"},
            {"species": "Juncus gerardii", "weight": 0.85, "common_name": "Saltmarsh Rush"},
            {"species": "Festuca rubra", "weight": 0.75, "common_name": "Red Fescue"},
        ],
        "constant": [
            {"species": "Plantago maritima", "weight": 0.70, "common_name": "Sea Plantain"},
            {"species": "Armeria maritima", "weight": 0.65, "common_name": "Thrift"},
            {"species": "Glaux maritima", "weight": 0.60, "common_name": "Sea Milkwort"},
        ]
    },
    "MA223": {  # Atlantic lower saltmarsh
        "diagnostic": [
            {"species": "Salicornia europaea", "weight": 0.95, "common_name": "Common Glasswort"},
            {"species": "Spartina anglica", "weight": 0.90, "common_name": "Common Cord-grass"},
            {"species": "Suaeda maritima", "weight": 0.85, "common_name": "Annual Sea-blite"},
        ],
        "dominant": [
            {"species": "Puccinellia maritima", "weight": 0.90, "common_name": "Common Saltmarsh-grass"},
            {"species": "Spartina anglica", "weight": 0.85, "common_name": "Common Cord-grass"},
        ],
        "constant": [
            {"species": "Aster tripolium", "weight": 0.75, "common_name": "Sea Aster"},
            {"species": "Halimione portulacoides", "weight": 0.70, "common_name": "Sea Purslane"},
            {"species": "Spergularia marina", "weight": 0.65, "common_name": "Lesser Sea-spurrey"},
        ]
    },
    
    # =========================================================================
    # MIRES AND BOGS
    # =========================================================================
    "Q11": {  # Raised bog
        "diagnostic": [
            {"species": "Sphagnum magellanicum", "weight": 0.95, "common_name": "Magellanic Bogmoss"},
            {"species": "Sphagnum papillosum", "weight": 0.90, "common_name": "Papillose Bogmoss"},
            {"species": "Andromeda polifolia", "weight": 0.85, "common_name": "Bog Rosemary"},
            {"species": "Drosera rotundifolia", "weight": 0.80, "common_name": "Round-leaved Sundew"},
        ],
        "dominant": [
            {"species": "Sphagnum rubellum", "weight": 0.90, "common_name": "Red Bogmoss"},
            {"species": "Eriophorum vaginatum", "weight": 0.85, "common_name": "Hare's-tail Cottongrass"},
            {"species": "Calluna vulgaris", "weight": 0.80, "common_name": "Heather"},
        ],
        "constant": [
            {"species": "Erica tetralix", "weight": 0.75, "common_name": "Cross-leaved Heath"},
            {"species": "Vaccinium oxycoccos", "weight": 0.70, "common_name": "Cranberry"},
            {"species": "Narthecium ossifragum", "weight": 0.65, "common_name": "Bog Asphodel"},
        ]
    },
    "Q12": {  # Blanket bog
        "diagnostic": [
            {"species": "Sphagnum papillosum", "weight": 0.95, "common_name": "Papillose Bogmoss"},
            {"species": "Sphagnum capillifolium", "weight": 0.90, "common_name": "Red Bogmoss"},
            {"species": "Racomitrium lanuginosum", "weight": 0.85, "common_name": "Woolly Fringe-moss"},
            {"species": "Pleurozia purpurea", "weight": 0.80, "common_name": "Purple Spoonwort"},
        ],
        "dominant": [
            {"species": "Eriophorum vaginatum", "weight": 0.90, "common_name": "Hare's-tail Cottongrass"},
            {"species": "Calluna vulgaris", "weight": 0.85, "common_name": "Heather"},
            {"species": "Trichophorum germanicum", "weight": 0.80, "common_name": "Deergrass"},
        ],
        "constant": [
            {"species": "Erica tetralix", "weight": 0.75, "common_name": "Cross-leaved Heath"},
            {"species": "Narthecium ossifragum", "weight": 0.70, "common_name": "Bog Asphodel"},
            {"species": "Drosera rotundifolia", "weight": 0.65, "common_name": "Round-leaved Sundew"},
        ]
    },
    "Q21": {  # Valley mire
        "diagnostic": [
            {"species": "Sphagnum fallax", "weight": 0.95, "common_name": "Flat-topped Bogmoss"},
            {"species": "Sphagnum palustre", "weight": 0.90, "common_name": "Blunt-leaved Bogmoss"},
            {"species": "Menyanthes trifoliata", "weight": 0.85, "common_name": "Bogbean"},
            {"species": "Potentilla palustris", "weight": 0.80, "common_name": "Marsh Cinquefoil"},
        ],
        "dominant": [
            {"species": "Molinia caerulea", "weight": 0.90, "common_name": "Purple Moor-grass"},
            {"species": "Juncus acutiflorus", "weight": 0.85, "common_name": "Sharp-flowered Rush"},
        ],
        "constant": [
            {"species": "Carex rostrata", "weight": 0.75, "common_name": "Bottle Sedge"},
            {"species": "Hydrocotyle vulgaris", "weight": 0.70, "common_name": "Marsh Pennywort"},
            {"species": "Viola palustris", "weight": 0.65, "common_name": "Marsh Violet"},
        ]
    },
    "Q4": {  # Base-rich fen
        "diagnostic": [
            {"species": "Schoenus nigricans", "weight": 0.95, "common_name": "Black Bog-rush"},
            {"species": "Cladium mariscus", "weight": 0.90, "common_name": "Great Fen-sedge"},
            {"species": "Parnassia palustris", "weight": 0.85, "common_name": "Grass-of-Parnassus"},
            {"species": "Epipactis palustris", "weight": 0.80, "common_name": "Marsh Helleborine"},
        ],
        "dominant": [
            {"species": "Phragmites australis", "weight": 0.85, "common_name": "Common Reed"},
            {"species": "Cladium mariscus", "weight": 0.80, "common_name": "Great Fen-sedge"},
        ],
        "constant": [
            {"species": "Juncus subnodulosus", "weight": 0.75, "common_name": "Blunt-flowered Rush"},
            {"species": "Mentha aquatica", "weight": 0.70, "common_name": "Water Mint"},
            {"species": "Eupatorium cannabinum", "weight": 0.65, "common_name": "Hemp-agrimony"},
        ]
    },
    "Q41": {  # Alkaline, calcareous fen
        "diagnostic": [
            {"species": "Schoenus nigricans", "weight": 0.95, "common_name": "Black Bog-rush"},
            {"species": "Carex davalliana", "weight": 0.90, "common_name": "Davall's Sedge"},
            {"species": "Primula farinosa", "weight": 0.85, "common_name": "Bird's-eye Primrose"},
            {"species": "Tofieldia calyculata", "weight": 0.80, "common_name": "German Asphodel"},
        ],
        "dominant": [
            {"species": "Schoenus nigricans", "weight": 0.90, "common_name": "Black Bog-rush"},
            {"species": "Carex hostiana", "weight": 0.85, "common_name": "Tawny Sedge"},
        ],
        "constant": [
            {"species": "Parnassia palustris", "weight": 0.75, "common_name": "Grass-of-Parnassus"},
            {"species": "Pinguicula vulgaris", "weight": 0.70, "common_name": "Common Butterwort"},
            {"species": "Eriophorum latifolium", "weight": 0.65, "common_name": "Broad-leaved Cottongrass"},
        ]
    },
    "Q51": {  # Tall-sedge bed
        "diagnostic": [
            {"species": "Carex acutiformis", "weight": 0.95, "common_name": "Lesser Pond-sedge"},
            {"species": "Carex riparia", "weight": 0.90, "common_name": "Greater Pond-sedge"},
            {"species": "Carex paniculata", "weight": 0.85, "common_name": "Greater Tussock-sedge"},
        ],
        "dominant": [
            {"species": "Carex acutiformis", "weight": 0.90, "common_name": "Lesser Pond-sedge"},
            {"species": "Carex riparia", "weight": 0.85, "common_name": "Greater Pond-sedge"},
            {"species": "Carex elata", "weight": 0.80, "common_name": "Tufted Sedge"},
        ],
        "constant": [
            {"species": "Iris pseudacorus", "weight": 0.75, "common_name": "Yellow Iris"},
            {"species": "Lysimachia vulgaris", "weight": 0.70, "common_name": "Yellow Loosestrife"},
            {"species": "Lythrum salicaria", "weight": 0.65, "common_name": "Purple Loosestrife"},
        ]
    },
    
    # =========================================================================
    # GRASSLANDS
    # =========================================================================
    "R1A": {  # Semi-dry calcareous grassland
        "diagnostic": [
            {"species": "Bromus erectus", "weight": 0.90, "common_name": "Upright Brome"},
            {"species": "Hippocrepis comosa", "weight": 0.85, "common_name": "Horseshoe Vetch"},
            {"species": "Anthyllis vulneraria", "weight": 0.80, "common_name": "Kidney Vetch"},
            {"species": "Sanguisorba minor", "weight": 0.75, "common_name": "Salad Burnet"},
        ],
        "dominant": [
            {"species": "Bromus erectus", "weight": 0.90, "common_name": "Upright Brome"},
            {"species": "Brachypodium pinnatum", "weight": 0.80, "common_name": "Tor-grass"},
            {"species": "Festuca ovina", "weight": 0.75, "common_name": "Sheep's Fescue"},
        ],
        "constant": [
            {"species": "Thymus pulegioides", "weight": 0.70, "common_name": "Large Thyme"},
            {"species": "Carlina vulgaris", "weight": 0.65, "common_name": "Carline Thistle"},
            {"species": "Centaurea scabiosa", "weight": 0.60, "common_name": "Greater Knapweed"},
        ]
    },
    "R1B": {  # Heavy-metal grassland
        "diagnostic": [
            {"species": "Viola calaminaria", "weight": 0.95, "common_name": "Yellow Zinc Violet"},
            {"species": "Armeria maritima subsp. halleri", "weight": 0.90, "common_name": "Haller's Thrift"},
            {"species": "Silene vulgaris var. humilis", "weight": 0.85, "common_name": "Calamine Campion"},
            {"species": "Minuartia verna", "weight": 0.80, "common_name": "Spring Sandwort"},
        ],
        "dominant": [
            {"species": "Festuca ovina", "weight": 0.85, "common_name": "Sheep's Fescue"},
            {"species": "Agrostis capillaris", "weight": 0.80, "common_name": "Common Bent"},
        ],
        "constant": [
            {"species": "Rumex acetosa", "weight": 0.70, "common_name": "Common Sorrel"},
            {"species": "Plantago lanceolata", "weight": 0.65, "common_name": "Ribwort Plantain"},
            {"species": "Thymus pulegioides", "weight": 0.60, "common_name": "Large Thyme"},
        ]
    },
    "R21": {  # Mesic permanent pasture
        "diagnostic": [
            {"species": "Lolium perenne", "weight": 0.90, "common_name": "Perennial Ryegrass"},
            {"species": "Cynosurus cristatus", "weight": 0.85, "common_name": "Crested Dog's-tail"},
            {"species": "Trifolium repens", "weight": 0.80, "common_name": "White Clover"},
        ],
        "dominant": [
            {"species": "Lolium perenne", "weight": 0.90, "common_name": "Perennial Ryegrass"},
            {"species": "Poa pratensis", "weight": 0.85, "common_name": "Smooth Meadow-grass"},
            {"species": "Festuca pratensis", "weight": 0.80, "common_name": "Meadow Fescue"},
        ],
        "constant": [
            {"species": "Trifolium repens", "weight": 0.75, "common_name": "White Clover"},
            {"species": "Bellis perennis", "weight": 0.70, "common_name": "Daisy"},
            {"species": "Taraxacum officinale", "weight": 0.65, "common_name": "Dandelion"},
            {"species": "Plantago major", "weight": 0.60, "common_name": "Greater Plantain"},
        ]
    },
    "R22": {  # Low and medium altitude hay meadow
        "diagnostic": [
            {"species": "Arrhenatherum elatius", "weight": 0.90, "common_name": "False Oat-grass"},
            {"species": "Crepis biennis", "weight": 0.85, "common_name": "Rough Hawk's-beard"},
            {"species": "Tragopogon pratensis", "weight": 0.80, "common_name": "Goat's-beard"},
            {"species": "Knautia arvensis", "weight": 0.75, "common_name": "Field Scabious"},
        ],
        "dominant": [
            {"species": "Arrhenatherum elatius", "weight": 0.90, "common_name": "False Oat-grass"},
            {"species": "Dactylis glomerata", "weight": 0.85, "common_name": "Cock's-foot"},
            {"species": "Trisetum flavescens", "weight": 0.80, "common_name": "Yellow Oat-grass"},
        ],
        "constant": [
            {"species": "Leucanthemum vulgare", "weight": 0.75, "common_name": "Oxeye Daisy"},
            {"species": "Centaurea jacea", "weight": 0.70, "common_name": "Brown Knapweed"},
            {"species": "Galium mollugo", "weight": 0.65, "common_name": "Hedge Bedstraw"},
        ]
    },
    "R35": {  # Moist oligotrophic grassland
        "diagnostic": [
            {"species": "Cirsium dissectum", "weight": 0.90, "common_name": "Meadow Thistle"},
            {"species": "Succisa pratensis", "weight": 0.85, "common_name": "Devil's-bit Scabious"},
            {"species": "Juncus acutiflorus", "weight": 0.80, "common_name": "Sharp-flowered Rush"},
        ],
        "dominant": [
            {"species": "Molinia caerulea", "weight": 0.90, "common_name": "Purple Moor-grass"},
            {"species": "Juncus acutiflorus", "weight": 0.80, "common_name": "Sharp-flowered Rush"},
        ],
        "constant": [
            {"species": "Lotus pedunculatus", "weight": 0.70, "common_name": "Greater Bird's-foot Trefoil"},
            {"species": "Potentilla erecta", "weight": 0.65, "common_name": "Tormentil"},
            {"species": "Carex panicea", "weight": 0.60, "common_name": "Carnation Sedge"},
        ]
    },
    "R37": {  # Moist mesotrophic to eutrophic grassland
        "diagnostic": [
            {"species": "Caltha palustris", "weight": 0.90, "common_name": "Marsh-marigold"},
            {"species": "Cardamine pratensis", "weight": 0.85, "common_name": "Cuckooflower"},
            {"species": "Fritillaria meleagris", "weight": 0.80, "common_name": "Fritillary"},
            {"species": "Senecio aquaticus", "weight": 0.75, "common_name": "Marsh Ragwort"},
        ],
        "dominant": [
            {"species": "Alopecurus pratensis", "weight": 0.90, "common_name": "Meadow Foxtail"},
            {"species": "Holcus lanatus", "weight": 0.85, "common_name": "Yorkshire-fog"},
            {"species": "Poa trivialis", "weight": 0.80, "common_name": "Rough Meadow-grass"},
        ],
        "constant": [
            {"species": "Ranunculus acris", "weight": 0.75, "common_name": "Meadow Buttercup"},
            {"species": "Rumex acetosa", "weight": 0.70, "common_name": "Common Sorrel"},
            {"species": "Lychnis flos-cuculi", "weight": 0.65, "common_name": "Ragged-robin"},
        ]
    },
    
    # =========================================================================
    # HEATHLANDS
    # =========================================================================
    "S31": {  # Atlantic wet heath
        "diagnostic": [
            {"species": "Erica tetralix", "weight": 0.95, "common_name": "Cross-leaved Heath"},
            {"species": "Narthecium ossifragum", "weight": 0.90, "common_name": "Bog Asphodel"},
            {"species": "Drosera intermedia", "weight": 0.85, "common_name": "Oblong-leaved Sundew"},
        ],
        "dominant": [
            {"species": "Erica tetralix", "weight": 0.90, "common_name": "Cross-leaved Heath"},
            {"species": "Molinia caerulea", "weight": 0.85, "common_name": "Purple Moor-grass"},
            {"species": "Calluna vulgaris", "weight": 0.80, "common_name": "Heather"},
        ],
        "constant": [
            {"species": "Potentilla erecta", "weight": 0.75, "common_name": "Tormentil"},
            {"species": "Juncus squarrosus", "weight": 0.70, "common_name": "Heath Rush"},
            {"species": "Carex panicea", "weight": 0.65, "common_name": "Carnation Sedge"},
        ]
    },
    "S41": {  # Atlantic dry heath
        "diagnostic": [
            {"species": "Calluna vulgaris", "weight": 0.95, "common_name": "Heather"},
            {"species": "Erica cinerea", "weight": 0.90, "common_name": "Bell Heather"},
            {"species": "Genista anglica", "weight": 0.80, "common_name": "Petty Whin"},
        ],
        "dominant": [
            {"species": "Calluna vulgaris", "weight": 0.95, "common_name": "Heather"},
            {"species": "Erica cinerea", "weight": 0.85, "common_name": "Bell Heather"},
            {"species": "Ulex europaeus", "weight": 0.75, "common_name": "Gorse"},
        ],
        "constant": [
            {"species": "Deschampsia flexuosa", "weight": 0.70, "common_name": "Wavy Hair-grass"},
            {"species": "Carex pilulifera", "weight": 0.65, "common_name": "Pill Sedge"},
            {"species": "Potentilla erecta", "weight": 0.60, "common_name": "Tormentil"},
        ]
    },
    "S42": {  # Continental dry heath
        "diagnostic": [
            {"species": "Calluna vulgaris", "weight": 0.95, "common_name": "Heather"},
            {"species": "Genista pilosa", "weight": 0.90, "common_name": "Hairy Greenweed"},
            {"species": "Genista germanica", "weight": 0.85, "common_name": "German Greenweed"},
        ],
        "dominant": [
            {"species": "Calluna vulgaris", "weight": 0.95, "common_name": "Heather"},
            {"species": "Vaccinium myrtillus", "weight": 0.80, "common_name": "Bilberry"},
        ],
        "constant": [
            {"species": "Deschampsia flexuosa", "weight": 0.75, "common_name": "Wavy Hair-grass"},
            {"species": "Festuca ovina", "weight": 0.70, "common_name": "Sheep's Fescue"},
            {"species": "Hieracium pilosella", "weight": 0.65, "common_name": "Mouse-ear Hawkweed"},
        ]
    },
    
    # =========================================================================
    # FORESTS
    # =========================================================================
    "T11": {  # Temperate Salix and Populus riparian forest
        "diagnostic": [
            {"species": "Salix alba", "weight": 0.95, "common_name": "White Willow"},
            {"species": "Populus nigra", "weight": 0.90, "common_name": "Black Poplar"},
            {"species": "Salix fragilis", "weight": 0.85, "common_name": "Crack Willow"},
            {"species": "Populus alba", "weight": 0.80, "common_name": "White Poplar"},
        ],
        "dominant": [
            {"species": "Salix alba", "weight": 0.90, "common_name": "White Willow"},
            {"species": "Populus nigra", "weight": 0.85, "common_name": "Black Poplar"},
        ],
        "constant": [
            {"species": "Urtica dioica", "weight": 0.75, "common_name": "Common Nettle"},
            {"species": "Phalaris arundinacea", "weight": 0.70, "common_name": "Reed Canary-grass"},
            {"species": "Humulus lupulus", "weight": 0.65, "common_name": "Hop"},
        ]
    },
    "T12": {  # Temperate Fraxinus-Alnus forest
        "diagnostic": [
            {"species": "Alnus glutinosa", "weight": 0.95, "common_name": "Alder"},
            {"species": "Fraxinus excelsior", "weight": 0.90, "common_name": "Ash"},
            {"species": "Carex remota", "weight": 0.85, "common_name": "Remote Sedge"},
            {"species": "Chrysosplenium oppositifolium", "weight": 0.80, "common_name": "Opposite-leaved Golden-saxifrage"},
        ],
        "dominant": [
            {"species": "Alnus glutinosa", "weight": 0.95, "common_name": "Alder"},
            {"species": "Fraxinus excelsior", "weight": 0.85, "common_name": "Ash"},
        ],
        "constant": [
            {"species": "Filipendula ulmaria", "weight": 0.75, "common_name": "Meadowsweet"},
            {"species": "Caltha palustris", "weight": 0.70, "common_name": "Marsh-marigold"},
            {"species": "Cardamine amara", "weight": 0.65, "common_name": "Large Bitter-cress"},
        ]
    },
    "T13": {  # Temperate hardwood riparian forest
        "diagnostic": [
            {"species": "Ulmus laevis", "weight": 0.95, "common_name": "European White Elm"},
            {"species": "Ulmus minor", "weight": 0.90, "common_name": "Field Elm"},
            {"species": "Quercus robur", "weight": 0.85, "common_name": "Pedunculate Oak"},
            {"species": "Fraxinus excelsior", "weight": 0.80, "common_name": "Ash"},
        ],
        "dominant": [
            {"species": "Quercus robur", "weight": 0.90, "common_name": "Pedunculate Oak"},
            {"species": "Fraxinus excelsior", "weight": 0.85, "common_name": "Ash"},
            {"species": "Ulmus minor", "weight": 0.80, "common_name": "Field Elm"},
        ],
        "constant": [
            {"species": "Anemone nemorosa", "weight": 0.75, "common_name": "Wood Anemone"},
            {"species": "Ranunculus ficaria", "weight": 0.70, "common_name": "Lesser Celandine"},
            {"species": "Corydalis cava", "weight": 0.65, "common_name": "Hollowroot"},
        ]
    },
    "T17": {  # Fagus forest on non-acid soil
        "diagnostic": [
            {"species": "Fagus sylvatica", "weight": 0.95, "common_name": "European Beech"},
            {"species": "Galium odoratum", "weight": 0.85, "common_name": "Sweet Woodruff"},
            {"species": "Mercurialis perennis", "weight": 0.80, "common_name": "Dog's Mercury"},
            {"species": "Allium ursinum", "weight": 0.75, "common_name": "Wild Garlic"},
        ],
        "dominant": [
            {"species": "Fagus sylvatica", "weight": 0.95, "common_name": "European Beech"},
            {"species": "Fraxinus excelsior", "weight": 0.70, "common_name": "Ash"},
        ],
        "constant": [
            {"species": "Anemone nemorosa", "weight": 0.75, "common_name": "Wood Anemone"},
            {"species": "Lamiastrum galeobdolon", "weight": 0.70, "common_name": "Yellow Archangel"},
            {"species": "Viola reichenbachiana", "weight": 0.65, "common_name": "Early Dog-violet"},
        ]
    },
    "T18": {  # Fagus forest on acid soil
        "diagnostic": [
            {"species": "Fagus sylvatica", "weight": 0.95, "common_name": "European Beech"},
            {"species": "Luzula luzuloides", "weight": 0.90, "common_name": "White Woodrush"},
            {"species": "Deschampsia flexuosa", "weight": 0.85, "common_name": "Wavy Hair-grass"},
        ],
        "dominant": [
            {"species": "Fagus sylvatica", "weight": 0.95, "common_name": "European Beech"},
            {"species": "Quercus petraea", "weight": 0.75, "common_name": "Sessile Oak"},
        ],
        "constant": [
            {"species": "Vaccinium myrtillus", "weight": 0.75, "common_name": "Bilberry"},
            {"species": "Pteridium aquilinum", "weight": 0.70, "common_name": "Bracken"},
            {"species": "Maianthemum bifolium", "weight": 0.65, "common_name": "May Lily"},
        ]
    },
    "T1F": {  # Broadleaved swamp forest on acid peat
        "diagnostic": [
            {"species": "Betula pubescens", "weight": 0.95, "common_name": "Downy Birch"},
            {"species": "Alnus glutinosa", "weight": 0.90, "common_name": "Alder"},
            {"species": "Sphagnum palustre", "weight": 0.85, "common_name": "Blunt-leaved Bogmoss"},
            {"species": "Thelypteris palustris", "weight": 0.80, "common_name": "Marsh Fern"},
        ],
        "dominant": [
            {"species": "Betula pubescens", "weight": 0.90, "common_name": "Downy Birch"},
            {"species": "Alnus glutinosa", "weight": 0.85, "common_name": "Alder"},
        ],
        "constant": [
            {"species": "Carex elongata", "weight": 0.75, "common_name": "Elongated Sedge"},
            {"species": "Calla palustris", "weight": 0.70, "common_name": "Bog Arum"},
            {"species": "Solanum dulcamara", "weight": 0.65, "common_name": "Bittersweet"},
        ]
    },
    "T1H": {  # Temperate Quercus forest
        "diagnostic": [
            {"species": "Quercus robur", "weight": 0.95, "common_name": "Pedunculate Oak"},
            {"species": "Quercus petraea", "weight": 0.90, "common_name": "Sessile Oak"},
            {"species": "Stellaria holostea", "weight": 0.75, "common_name": "Greater Stitchwort"},
        ],
        "dominant": [
            {"species": "Quercus robur", "weight": 0.95, "common_name": "Pedunculate Oak"},
            {"species": "Quercus petraea", "weight": 0.90, "common_name": "Sessile Oak"},
            {"species": "Betula pendula", "weight": 0.70, "common_name": "Silver Birch"},
        ],
        "constant": [
            {"species": "Lonicera periclymenum", "weight": 0.75, "common_name": "Honeysuckle"},
            {"species": "Pteridium aquilinum", "weight": 0.70, "common_name": "Bracken"},
            {"species": "Deschampsia flexuosa", "weight": 0.65, "common_name": "Wavy Hair-grass"},
        ]
    },
    "T3F": {  # Picea forest on acid soil
        "diagnostic": [
            {"species": "Picea abies", "weight": 0.95, "common_name": "Norway Spruce"},
            {"species": "Bazzania trilobata", "weight": 0.90, "common_name": "Greater Whipwort"},
            {"species": "Sphagnum girgensohnii", "weight": 0.85, "common_name": "Girgensohn's Bogmoss"},
        ],
        "dominant": [
            {"species": "Picea abies", "weight": 0.95, "common_name": "Norway Spruce"},
            {"species": "Vaccinium myrtillus", "weight": 0.80, "common_name": "Bilberry"},
        ],
        "constant": [
            {"species": "Deschampsia flexuosa", "weight": 0.75, "common_name": "Wavy Hair-grass"},
            {"species": "Oxalis acetosella", "weight": 0.70, "common_name": "Wood Sorrel"},
            {"species": "Dicranum scoparium", "weight": 0.65, "common_name": "Broom Fork-moss"},
        ]
    },
    "T3G": {  # Pinus sylvestris forest
        "diagnostic": [
            {"species": "Pinus sylvestris", "weight": 0.95, "common_name": "Scots Pine"},
            {"species": "Pyrola minor", "weight": 0.85, "common_name": "Common Wintergreen"},
            {"species": "Monotropa hypopitys", "weight": 0.80, "common_name": "Yellow Bird's-nest"},
        ],
        "dominant": [
            {"species": "Pinus sylvestris", "weight": 0.95, "common_name": "Scots Pine"},
            {"species": "Calluna vulgaris", "weight": 0.80, "common_name": "Heather"},
        ],
        "constant": [
            {"species": "Vaccinium myrtillus", "weight": 0.75, "common_name": "Bilberry"},
            {"species": "Vaccinium vitis-idaea", "weight": 0.70, "common_name": "Cowberry"},
            {"species": "Deschampsia flexuosa", "weight": 0.65, "common_name": "Wavy Hair-grass"},
            {"species": "Pleurozium schreberi", "weight": 0.60, "common_name": "Schreber's Big Red Stem Moss"},
        ]
    },
}

# Build species lookup table (species -> habitats it indicates)
SPECIES_TO_HABITATS = {}
for hab_code, indicators in INDICATOR_SPECIES.items():
    for species_type in ["diagnostic", "dominant", "constant"]:
        for sp in indicators.get(species_type, []):
            species_name = sp["species"]
            if species_name not in SPECIES_TO_HABITATS:
                SPECIES_TO_HABITATS[species_name] = []
            SPECIES_TO_HABITATS[species_name].append({
                "habitat_code": hab_code,
                "habitat_name": EUNIS_HABITATS[hab_code]["name"],
                "indicator_type": species_type,
                "weight": sp["weight"]
            })

# All unique species names for autocomplete
ALL_SPECIES = sorted(list(SPECIES_TO_HABITATS.keys()))

# Sample observation coordinates for Netherlands visualization (EPSG:4326)
# In full plugin: 98M+ records from spatial tables
SAMPLE_OBSERVATIONS_NL = {
    "N10": [  # Sand beach - North Sea coast
        {"lat": 53.20, "lon": 4.85, "score": 0.88, "year": 2010},
        {"lat": 52.95, "lon": 4.72, "score": 0.85, "year": 2010},
        {"lat": 52.45, "lon": 4.55, "score": 0.82, "year": 2000},
    ],
    "MA222": [  # Atlantic upper saltmarsh - Wadden Sea area
        {"lat": 53.45, "lon": 5.75, "score": 0.92, "year": 2010},
        {"lat": 53.40, "lon": 5.65, "score": 0.88, "year": 2010},
        {"lat": 53.35, "lon": 5.80, "score": 0.85, "year": 2010},
        {"lat": 53.42, "lon": 6.10, "score": 0.90, "year": 2010},
        {"lat": 53.38, "lon": 6.25, "score": 0.87, "year": 2010},
        {"lat": 53.30, "lon": 5.55, "score": 0.82, "year": 2000},
        {"lat": 53.25, "lon": 5.70, "score": 0.78, "year": 2000},
        {"lat": 51.65, "lon": 4.05, "score": 0.85, "year": 2010},
        {"lat": 51.58, "lon": 3.95, "score": 0.80, "year": 2010},
    ],
    "Q11": [  # Raised bog - Drenthe/Overijssel
        {"lat": 52.85, "lon": 6.75, "score": 0.90, "year": 2010},
        {"lat": 52.80, "lon": 6.80, "score": 0.88, "year": 2010},
        {"lat": 52.75, "lon": 6.70, "score": 0.85, "year": 2010},
        {"lat": 52.90, "lon": 6.65, "score": 0.82, "year": 2000},
        {"lat": 52.70, "lon": 6.90, "score": 0.78, "year": 2000},
    ],
    "S41": [  # Atlantic dry heath - Veluwe
        {"lat": 52.15, "lon": 5.85, "score": 0.92, "year": 2010},
        {"lat": 52.20, "lon": 5.90, "score": 0.88, "year": 2010},
        {"lat": 52.10, "lon": 5.80, "score": 0.85, "year": 2010},
        {"lat": 52.25, "lon": 5.95, "score": 0.90, "year": 2010},
        {"lat": 52.05, "lon": 5.75, "score": 0.80, "year": 2000},
        {"lat": 52.30, "lon": 6.00, "score": 0.75, "year": 2000},
    ],
    "S31": [  # Atlantic wet heath - Veluwe/Drenthe
        {"lat": 52.40, "lon": 6.20, "score": 0.88, "year": 2010},
        {"lat": 52.35, "lon": 6.15, "score": 0.85, "year": 2010},
        {"lat": 52.45, "lon": 6.25, "score": 0.82, "year": 2000},
    ],
    "T17": [  # Beech forest - Limburg hills
        {"lat": 50.85, "lon": 5.90, "score": 0.95, "year": 2010},
        {"lat": 50.80, "lon": 5.85, "score": 0.92, "year": 2010},
        {"lat": 50.82, "lon": 5.95, "score": 0.88, "year": 2010},
        {"lat": 50.78, "lon": 5.80, "score": 0.85, "year": 2000},
    ],
    "T1H": [  # Oak forest - Veluwe/Limburg
        {"lat": 52.08, "lon": 5.92, "score": 0.90, "year": 2010},
        {"lat": 52.12, "lon": 5.88, "score": 0.87, "year": 2010},
        {"lat": 50.90, "lon": 5.82, "score": 0.85, "year": 2000},
    ],
    "R1A": [  # Calcareous grassland - Limburg
        {"lat": 50.88, "lon": 5.75, "score": 0.90, "year": 2010},
        {"lat": 50.85, "lon": 5.80, "score": 0.88, "year": 2010},
        {"lat": 50.82, "lon": 5.70, "score": 0.82, "year": 2000},
    ],
    "R35": [  # Moist oligotrophic grassland
        {"lat": 52.55, "lon": 5.45, "score": 0.87, "year": 2010},
        {"lat": 52.50, "lon": 5.50, "score": 0.84, "year": 2010},
        {"lat": 52.60, "lon": 5.40, "score": 0.80, "year": 2000},
    ],
    "T12": [  # Alder-Ash forest
        {"lat": 52.35, "lon": 5.25, "score": 0.88, "year": 2010},
        {"lat": 52.30, "lon": 5.30, "score": 0.85, "year": 2010},
        {"lat": 51.95, "lon": 5.85, "score": 0.82, "year": 2000},
    ],
    "T3G": [  # Pine forest - Veluwe
        {"lat": 52.18, "lon": 5.78, "score": 0.92, "year": 2010},
        {"lat": 52.22, "lon": 5.82, "score": 0.89, "year": 2010},
        {"lat": 52.15, "lon": 5.75, "score": 0.86, "year": 2000},
    ],
}


# ============================================================================
# CORE ALGORITHM - HABITAT PREDICTION
# ============================================================================

def predict_habitat_from_species(species_list: List[str], threshold: float = 0.3) -> List[Dict]:
    """
    Core EPDV algorithm: Predict EUNIS habitat type from a list of species.
    
    Algorithm:
    1. For each habitat type, calculate score based on indicator species present
    2. Weight by indicator type (diagnostic > dominant > constant)
    3. Return habitats exceeding threshold, sorted by score
    """
    
    results = []
    
    # Normalize input species names
    species_list_normalized = [s.strip() for s in species_list if s.strip()]
    
    for hab_code, indicators in INDICATOR_SPECIES.items():
        if not any(indicators.values()):  # Skip habitats without indicator data
            continue
            
        score = 0.0
        matched_species = {"diagnostic": [], "dominant": [], "constant": []}
        
        # Weight multipliers for indicator types
        type_weights = {"diagnostic": 1.5, "dominant": 1.2, "constant": 1.0}
        
        total_possible = 0
        
        for indicator_type, species_data in indicators.items():
            type_weight = type_weights.get(indicator_type, 1.0)
            
            for sp in species_data:
                total_possible += sp["weight"] * type_weight
                
                # Check if species is in input list (case-insensitive partial match)
                for input_sp in species_list_normalized:
                    if input_sp.lower() in sp["species"].lower() or sp["species"].lower() in input_sp.lower():
                        score += sp["weight"] * type_weight
                        matched_species[indicator_type].append(sp)
                        break
        
        # Normalize score
        if total_possible > 0:
            normalized_score = score / total_possible
        else:
            normalized_score = 0.0
        
        if normalized_score >= threshold:
            results.append({
                "habitat_code": hab_code,
                "habitat_name": EUNIS_HABITATS[hab_code]["name"],
                "score": round(normalized_score, 3),
                "matched_species": matched_species,
                "total_matched": sum(len(v) for v in matched_species.values())
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_habitat_map(habitat_code: str, year_filter: Optional[int] = None) -> folium.Map:
    """Create a Folium map showing habitat distribution."""
    
    # Center on Netherlands
    m = folium.Map(
        location=[52.2, 5.5],
        zoom_start=7,
        tiles="cartodbpositron"
    )
    
    observations = SAMPLE_OBSERVATIONS_NL.get(habitat_code, [])
    
    if year_filter:
        observations = [o for o in observations if o["year"] == year_filter]
    
    if not observations:
        return m
    
    # Add markers
    for obs in observations:
        color = "#2ca02c" if obs["score"] >= 0.85 else "#ffbb00" if obs["score"] >= 0.70 else "#d62728"
        
        folium.CircleMarker(
            location=[obs["lat"], obs["lon"]],
            radius=8 + (obs["score"] * 10),
            popup=f"Score: {obs['score']:.2f}<br>Year: {obs['year']}",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
        ).add_to(m)
    
    # Add heatmap
    if len(observations) > 3:
        heat_data = [[o["lat"], o["lon"], o["score"]] for o in observations]
        HeatMap(heat_data, radius=25, blur=15).add_to(m)
    
    return m


def create_indicator_chart(indicators: Dict) -> go.Figure:
    """Create a bar chart showing indicator species and their weights."""
    
    all_species = []
    for ind_type, color in [("diagnostic", "#d62728"), ("dominant", "#ff7f0e"), ("constant", "#2ca02c")]:
        for sp in indicators.get(ind_type, []):
            all_species.append({
                "species": sp["species"],
                "weight": sp["weight"],
                "type": ind_type.capitalize(),
                "color": color
            })
    
    if not all_species:
        return go.Figure()
    
    df = pd.DataFrame(all_species)
    
    fig = go.Figure()
    
    for ind_type, color in [("Diagnostic", "#d62728"), ("Dominant", "#ff7f0e"), ("Constant", "#2ca02c")]:
        subset = df[df["type"] == ind_type]
        if not subset.empty:
            fig.add_trace(go.Bar(
                y=subset["species"],
                x=subset["weight"],
                orientation="h",
                name=ind_type,
                marker_color=color,
            ))
    
    fig.update_layout(
        title="Indicator Species Weights",
        xaxis_title="Weight",
        yaxis_title="",
        barmode="group",
        height=400,
        margin=dict(l=200),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    
    return fig


def create_prediction_chart(predictions: List[Dict]) -> go.Figure:
    """Create a bar chart showing habitat prediction scores."""
    
    if not predictions:
        return go.Figure()
    
    df = pd.DataFrame(predictions)
    
    colors = ["#2ca02c" if s >= 0.7 else "#ffbb00" if s >= 0.4 else "#d62728" for s in df["score"]]
    
    fig = go.Figure(data=[go.Bar(
        x=df["score"],
        y=[f"{r['habitat_code']}: {r['habitat_name'][:30]}..." for _, r in df.iterrows()],
        orientation="h",
        marker_color=colors,
        text=[f"{s:.1%}" for s in df["score"]],
        textposition="outside",
    )])
    
    fig.update_layout(
        title="Predicted Habitat Types",
        xaxis_title="Prediction Score",
        xaxis=dict(range=[0, 1.1], tickformat=".0%"),
        yaxis_title="",
        height=300 + len(predictions) * 40,
        margin=dict(l=250),
    )
    
    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.title("EPDV - EUNIS Habitat Predictor")
    st.markdown("### EUNIS Proxy Distribution Viewer - Web Demo")
    st.markdown(
        "*Developed by [Mohamed Z. Hatim](mailto:mohamed.hatim@wur.nl), "
        "Wageningen University & Research, in collaboration with "
        "**WENR Team Earth Observation & Environmental Informatics***"
    )
    st.markdown("---")
    
    # Sidebar - Mode Selection
    with st.sidebar:
        st.header("Analysis Mode")
        
        mode = st.radio(
            "Select function:",
            [
                "Predict Habitat from Species",
                "Browse EUNIS Habitats",
                "View Habitat Distribution",
                "Database Statistics"
            ],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### About EPDV")
        st.markdown(
            "The EUNIS Proxy Distribution Viewer predicts habitat types "
            "based on **98+ million** species observations across Europe."
        )
        st.markdown(
            "**Full QGIS plugin features:**\n"
            "- 10m/100m resolution\n"
            "- Temporal comparison (2000-2010)\n"
            "- EU Article 17 reporting\n"
            "- Connectivity analysis\n"
            "- Export to multiple formats"
        )
        st.markdown("---")
        st.markdown(
            "**Data sources:**\n"
            "- GBIF (16,653 species)\n"
            "- European Vegetation Archive\n"
            "- EUNIS habitat classification"
        )
        
        st.markdown("---")
        st.markdown(
            f"**Demo statistics:**\n"
            f"- Habitat types: {len(EUNIS_HABITATS)}\n"
            f"- Indicator species: {len(ALL_SPECIES)}\n"
            f"- Species-habitat links: {sum(len(v) for v in SPECIES_TO_HABITATS.values())}"
        )
    
    # Main content based on mode
    if "Predict Habitat" in mode:
        st.subheader("Habitat Prediction from Species List")
        st.markdown(
            "Enter a list of species observed at a location. "
            "The algorithm will predict the most likely EUNIS habitat type."
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Species input
            species_input = st.text_area(
                "Enter species (one per line):",
                placeholder="Calluna vulgaris\nErica cinerea\nDeschampsia flexuosa\nPotentilla erecta",
                height=200,
            )
            
            # Quick examples
            st.markdown("**Quick examples:**")
            example_col1, example_col2, example_col3, example_col4 = st.columns(4)

            with example_col1:
                if st.button("Saltmarsh"):
                    st.session_state["species_example"] = "Limonium vulgare\nPuccinellia maritima\nAster tripolium\nPlantago maritima\nArmeria maritima"

            with example_col2:
                if st.button("Dry heath"):
                    st.session_state["species_example"] = "Calluna vulgaris\nErica cinerea\nDeschampsia flexuosa\nCarex pilulifera\nPotentilla erecta"

            with example_col3:
                if st.button("Beech forest"):
                    st.session_state["species_example"] = "Fagus sylvatica\nGalium odoratum\nMercurialis perennis\nAnemone nemorosa\nAllium ursinum"
            
            with example_col4:
                if st.button("Raised bog"):
                    st.session_state["species_example"] = "Sphagnum magellanicum\nAndromeda polifolia\nDrosera rotundifolia\nEriophorum vaginatum\nVaccinium oxycoccos"
            
            if "species_example" in st.session_state:
                species_input = st.session_state["species_example"]
                st.text_area("Species list:", value=species_input, height=150, disabled=True)
        
        with col2:
            threshold = st.slider(
                "Prediction threshold:",
                min_value=0.1,
                max_value=0.9,
                value=0.3,
                step=0.1,
                help="Minimum score to include a habitat in results"
            )
        
        if st.button("Predict Habitat", type="primary"):
            if species_input.strip():
                species_list = [s.strip() for s in species_input.strip().split("\n") if s.strip()]
                
                with st.spinner("Analyzing species composition..."):
                    predictions = predict_habitat_from_species(species_list, threshold)
                
                if predictions:
                    st.success(f"Found {len(predictions)} matching habitat type(s)!")
                    
                    # Show predictions chart
                    st.plotly_chart(create_prediction_chart(predictions), use_container_width=True)
                    
                    # Detailed results
                    st.subheader("Detailed Results")
                    
                    for i, pred in enumerate(predictions[:5]):  # Top 5
                        with st.expander(f"**{pred['habitat_code']}**: {pred['habitat_name']} - Score: {pred['score']:.1%}", expanded=(i==0)):
                            st.markdown(f"**Description:** {EUNIS_HABITATS[pred['habitat_code']]['description']}")
                            st.markdown(f"**Matched species:** {pred['total_matched']}")
                            
                            for ind_type in ["diagnostic", "dominant", "constant"]:
                                matched = pred["matched_species"].get(ind_type, [])
                                if matched:
                                    st.markdown(f"*{ind_type.capitalize()}:* " + ", ".join([s["species"] for s in matched]))
                else:
                    st.warning("No habitat types matched with the given threshold. Try lowering the threshold or adding more species.")
            else:
                st.error("Please enter at least one species name.")
    
    elif "Browse EUNIS" in mode:
        st.subheader("EUNIS Habitat Browser")
        
        # Habitat selection
        habitat_options = {f"{code}: {info['name']}": code for code, info in EUNIS_HABITATS.items()}
        selected = st.selectbox("Select habitat type:", options=list(habitat_options.keys()))
        
        if selected:
            hab_code = habitat_options[selected]
            hab_info = EUNIS_HABITATS[hab_code]
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"### {hab_code}: {hab_info['name']}")
                st.markdown(f"**Description:** {hab_info['description']}")
                st.markdown(f"**EUNIS Level:** {hab_info['level']}")
                
                # Indicator species
                indicators = INDICATOR_SPECIES.get(hab_code, {})
                
                if any(indicators.values()):
                    st.markdown("---")
                    st.markdown("### Indicator Species")
                    
                    for ind_type, label in [("diagnostic", "[D]"), ("dominant", "[Dom]"), ("constant", "[C]")]:
                        species_list = indicators.get(ind_type, [])
                        if species_list:
                            st.markdown(f"**{label} {ind_type.capitalize()}:**")
                            for sp in species_list:
                                st.markdown(f"- *{sp['species']}* ({sp.get('common_name', '')}) - weight: {sp['weight']:.2f}")
                else:
                    st.info("Indicator species data not available for this habitat in the demo. Full plugin contains complete data.")
            
            with col2:
                if any(indicators.values()):
                    st.plotly_chart(create_indicator_chart(indicators), use_container_width=True)
    
    elif "View Habitat Distribution" in mode:
        st.subheader("Habitat Distribution Map")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Only show habitats with sample data
            habitats_with_data = [code for code in SAMPLE_OBSERVATIONS_NL.keys()]
            habitat_options = {f"{code}: {EUNIS_HABITATS[code]['name'][:30]}...": code for code in habitats_with_data}
            
            selected = st.selectbox("Select habitat:", options=list(habitat_options.keys()))
            
            year_filter = st.radio("Year filter:", ["All years", "2000", "2010"])
            year_val = None if year_filter == "All years" else int(year_filter)
            
            if selected:
                hab_code = habitat_options[selected]
                obs = SAMPLE_OBSERVATIONS_NL.get(hab_code, [])
                if year_val:
                    obs = [o for o in obs if o["year"] == year_val]
                
                st.metric("Observations", len(obs))
                if obs:
                    avg_score = sum(o["score"] for o in obs) / len(obs)
                    st.metric("Avg. Score", f"{avg_score:.1%}")
        
        with col2:
            if selected:
                hab_code = habitat_options[selected]
                m = create_habitat_map(hab_code, year_val)
                st_folium(m, width=700, height=500)
                
                st.caption("Green: High confidence (>=85%) | Yellow: Medium (70-85%) | Red: Lower (<70%)")
    
    elif "Database Statistics" in mode:
        st.subheader("EPDV Database Statistics")
        
        st.markdown("### Full Database (QGIS Plugin)")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Observations", "98.2M", help="98,162,156 species observations")
        with col2:
            st.metric("Species", "16,653", help="From GBIF taxonomy")
        with col3:
            st.metric("Habitat Types", "200+", help="EUNIS classification")
        with col4:
            st.metric("EVA Plots", "224,731", help="Validated ground-truth data")
        
        st.markdown("---")
        
        st.markdown("### Data Tables")
        
        table_data = pd.DataFrame([
            {"Table": "_10m_y2000", "Records": "22.8M", "Resolution": "10m", "Year": 2000},
            {"Table": "_10m_y2010", "Records": "17.8M", "Resolution": "10m", "Year": 2010},
            {"Table": "_100m_y2000", "Records": "32.3M", "Resolution": "100m", "Year": 2000},
            {"Table": "_100m_y2010", "Records": "25.3M", "Resolution": "100m", "Year": 2010},
        ])
        st.dataframe(table_data, use_container_width=True)
        
        st.markdown("---")
        
        st.markdown("### This Demo")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Habitat Types", len(EUNIS_HABITATS))
        with col2:
            st.metric("Indicator Species", len(ALL_SPECIES))
        with col3:
            st.metric("Species-Habitat Links", sum(len(v) for v in SPECIES_TO_HABITATS.values()))
        
        #st.markdown("---")
        
        #st.markdown("### Algorithm")
        #st.code("""
#For each grid cell (x, y):
    #1. Identify all species observed at location
    #2. For target habitat type:
       #- Get diagnostic species and their weights (multiplier: 1.5x)
       #- Get dominant species and their weights (multiplier: 1.2x)
       #- Get constant species and their weights (multiplier: 1.0x)
   # 3. Calculate score:
       #score = Sum(species_weight x type_multiplier x presence) / total_possible
    #4. If score >= threshold:
       #- Mark cell as potential habitat
       #- Store probability score
   # 5. Return georeferenced results
       # """, language="python")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "EPDV Web Demo | "
        "Full QGIS plugin in development with WENR Team Earth Informatics | "
        "2025 Mohamed Z. Hatim, Wageningen University & Research"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
