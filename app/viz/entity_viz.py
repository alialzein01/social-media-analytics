"""
Entity Visualization Module
============================

Visualizations for Named Entity Recognition results.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
from collections import Counter

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from app.styles.theme import THEME_COLORS


def create_entity_summary_card(entity_summary: Dict) -> None:
    """
    Display entity extraction summary with metrics.

    Args:
        entity_summary: Dictionary from EntityExtractor.summarize_entities()
    """
    st.markdown("#### 🏷️ Entity Extraction Summary")

    total = entity_summary.get('total_entities', 0)

    if total == 0:
        st.info("No entities found in the text.")
        return

    # Display metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Entities", f"{total:,}")

    with col2:
        entity_types = entity_summary.get('entity_types', {})
        st.metric("Entity Types", len(entity_types))

    with col3:
        unique_counts = entity_summary.get('unique_entities_by_type', {})
        total_unique = sum(unique_counts.values())
        st.metric("Unique Entities", f"{total_unique:,}")


def create_entity_type_chart(entity_summary: Dict) -> None:
    """
    Create bar chart showing distribution of entity types.

    Args:
        entity_summary: Dictionary from EntityExtractor.summarize_entities()
    """
    entity_types = entity_summary.get('entity_types', {})

    if not entity_types:
        return

    # Sort by count
    sorted_types = sorted(entity_types.items(), key=lambda x: x[1], reverse=True)

    df = pd.DataFrame(sorted_types, columns=['Entity Type', 'Count'])

    if PLOTLY_AVAILABLE:
        fig = px.bar(
            df,
            x='Count',
            y='Entity Type',
            orientation='h',
            title="Entity Types Distribution",
            color='Count',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text'],
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(df.set_index('Entity Type'))


def create_top_entities_tables(entity_summary: Dict, max_per_type: int = 10) -> None:
    """
    Display tables of top entities by type.

    Args:
        entity_summary: Dictionary from EntityExtractor.summarize_entities()
        max_per_type: Maximum entities to show per type
    """
    top_entities = entity_summary.get('top_entities', {})

    if not top_entities:
        return

    st.markdown("#### 🔝 Top Entities by Type")

    # Create columns for different entity types (max 2 per row)
    entity_types = list(top_entities.keys())

    for i in range(0, len(entity_types), 2):
        cols = st.columns(2)

        for j, col in enumerate(cols):
            if i + j < len(entity_types):
                entity_type = entity_types[i + j]
                entities = top_entities[entity_type]

                with col:
                    st.markdown(f"**{entity_type.title()}**")

                    if entities:
                        # Create DataFrame
                        df = pd.DataFrame(
                            list(entities.items())[:max_per_type],
                            columns=['Entity', 'Count']
                        )

                        # Display as table
                        st.dataframe(
                            df,
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.info(f"No {entity_type} entities found")


def create_entity_network_chart(entity_summary: Dict) -> None:
    """
    Create interactive sunburst chart showing entity hierarchy.

    Args:
        entity_summary: Dictionary from EntityExtractor.summarize_entities()
    """
    if not PLOTLY_AVAILABLE:
        return

    top_entities = entity_summary.get('top_entities', {})

    if not top_entities:
        return

    st.markdown("#### 🌐 Entity Hierarchy")

    # Prepare data for sunburst chart
    labels = []
    parents = []
    values = []

    # Root
    labels.append("All Entities")
    parents.append("")
    values.append(sum(sum(entities.values()) for entities in top_entities.values()))

    # Entity types
    for entity_type, entities in top_entities.items():
        type_total = sum(entities.values())
        labels.append(entity_type.title())
        parents.append("All Entities")
        values.append(type_total)

        # Individual entities (top 5 per type)
        for entity, count in list(entities.items())[:5]:
            labels.append(entity[:30])  # Truncate long names
            parents.append(entity_type.title())
            values.append(count)

    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(
            colorscale='Viridis',
            cmid=sum(values) / len(values)
        )
    ))

    fig.update_layout(
        height=600,
        paper_bgcolor=THEME_COLORS['background'],
        font_color=THEME_COLORS['text']
    )

    st.plotly_chart(fig, use_container_width=True)


def create_entity_wordcloud(entity_frequencies: Dict[str, int], entity_type: str = "Entities") -> None:
    """
    Create word cloud from entity frequencies.

    Args:
        entity_frequencies: Dictionary mapping entity text to frequency
        entity_type: Type of entities (for title)
    """
    if not entity_frequencies:
        return

    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt

        st.markdown(f"#### ☁️ {entity_type.title()} Word Cloud")

        # Generate word cloud
        wc = WordCloud(
            width=800,
            height=400,
            background_color=THEME_COLORS['background'],
            colormap='viridis',
            relative_scaling=0.5,
            min_font_size=10
        ).generate_from_frequencies(entity_frequencies)

        # Display
        fig, ax = plt.subplots(figsize=(12, 6), facecolor=THEME_COLORS['background'])
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        fig.patch.set_facecolor(THEME_COLORS['background'])

        st.pyplot(fig)

    except ImportError:
        # Fallback to simple list
        st.markdown(f"**Top {entity_type.title()}:**")
        for entity, count in list(entity_frequencies.items())[:20]:
            st.write(f"- {entity}: {count}")


def display_entity_dashboard(texts: List[str]) -> None:
    """
    Display comprehensive entity analysis dashboard.

    Args:
        texts: List of texts to analyze
    """
    try:
        from app.nlp.entity_extractor import extract_entities_summary, GLINER_AVAILABLE

        if not GLINER_AVAILABLE:
            st.warning("⚠️ GLiNER not available. Install with: `pip install gliner`")
            return

        if not texts:
            st.info("No text available for entity extraction")
            return

        with st.spinner("🔍 Extracting entities..."):
            # Extract entities
            entity_summary = extract_entities_summary(texts)

            if entity_summary['total_entities'] == 0:
                st.info("No entities found in the text")
                return

            # Display summary card
            create_entity_summary_card(entity_summary)

            st.markdown("---")

            # Display entity type distribution
            create_entity_type_chart(entity_summary)

            st.markdown("---")

            # Display top entities tables
            create_top_entities_tables(entity_summary)

            st.markdown("---")

            # Display entity hierarchy
            create_entity_network_chart(entity_summary)

    except Exception as e:
        st.error(f"Error in entity extraction: {str(e)}")
        st.info("Entity extraction feature is experimental. If you encounter issues, it can be disabled in settings.")
