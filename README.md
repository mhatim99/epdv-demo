# 🌿 EPDV - EUNIS Proxy Distribution Viewer

**Web Demo — EUNIS Habitat Prediction System**

A web-based demonstration of the EPDV QGIS plugin, developed in collaboration with WENR Team Earth Observation & Environmental Informatics at Wageningen University & Research.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🌐 Live Demo

**[Try the live demo →](https://epdv-demo.streamlit.app)**

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔮 **Habitat Prediction** | Input species list → Predict EUNIS habitat type |
| 📖 **Habitat Browser** | Explore 200+ EUNIS habitat types with indicator species |
| 🗺️ **Distribution Maps** | Visualize habitat distributions across the Netherlands |
| 📊 **Database Stats** | Overview of the 98M+ observation database |

## 🧬 The Algorithm

EPDV predicts EUNIS habitat types based on indicator species:

```python
For each habitat type:
    1. Check which diagnostic species are present (weight × 1.5)
    2. Check which dominant species are present (weight × 1.2)
    3. Check which constant species are present (weight × 1.0)
    4. Calculate normalized score
    5. Return habitats exceeding threshold
```

## 📊 Full Database (QGIS Plugin)

| Table | Records | Resolution | Year |
|-------|---------|------------|------|
| _10m_y2000 | 22.8M | 10m | 2000 |
| _10m_y2010 | 17.8M | 10m | 2010 |
| _100m_y2000 | 32.3M | 100m | 2000 |
| _100m_y2010 | 25.3M | 100m | 2010 |
| **Total** | **98.2M** | — | — |

Additional data:
- 16,653 species (GBIF taxonomy)
- 15,119 species-habitat indicator values
- 224,731 EVA validated plots

## 🚀 Quick Start

### Local Development

```bash
git clone https://github.com/yourusername/epdv-demo.git
cd epdv-demo
pip install -r requirements.txt
streamlit run app.py
```

### Deploy to Streamlit Cloud

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and deploy

## 🔗 Related

- **EUNIS Habitat Classification**: [European Environment Agency](https://www.eea.europa.eu/data-and-maps/data/eunis-habitat-classification-1)
- **GBIF**: [Global Biodiversity Information Facility](https://www.gbif.org/)
- **European Vegetation Archive**: [EVA Database](http://euroveg.org/eva-database)

## 👤 Author

**Mohamed Z. Hatim, PhD**  
Vegetation and Landscape Ecology  
Wageningen University & Research  

Developed in collaboration with:  
**WENR Team Earth Observation & Environmental Informatics**

📧 mohamed.hatim@wur.nl

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
