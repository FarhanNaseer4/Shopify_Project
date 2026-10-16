"""Category-specific source and Shopify rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryConfig:
    group: str
    name: str
    template_sheet: str
    source_sheet: str
    dimension_column: str | None
    title_prefix: str
    include_definition: bool = True
    thickness_column: str = "Stärke"
    area_column: str | None = None
    hint_column: str = "Hinweis"
    options: tuple[str, ...] = ("Material", "Stärke")
    price_mode: str = "single"
    source_filename_token: str = ""


CATEGORIES: dict[str, CategoryConfig] = {
    "Tafeln": {
        "Lochbleche": CategoryConfig("Tafeln", "Lochbleche", "Lochbleche", "qryDatenaustausch-Tafeln-Lochbl", "Lochgröße und -abstand", "Lochblech Tafelware", area_column="Ao, gelochte Fläche", options=("Material", "Stärke", "Format"), price_mode="tiers", source_filename_token="lochblech"),
        "Streckmetall": CategoryConfig("Tafeln", "Streckmetall", "Streckmetall", "Tabelle1", "Maschenlänge und -breite", "Streckmetall Tafelware", include_definition=False, area_column="Ao, ungelochte Fläche", options=("Material", "Stärke", "Format"), price_mode="tiers", source_filename_token="streckmetall"),
        "Schweißgitter": CategoryConfig("Tafeln", "Schweißgitter", "Schweißgitter", "Tabelle1", "Maschenweite", "Schweißgitter Tafelware", include_definition=False, thickness_column="Drahtstärke", area_column="Ao, ungelochte Fläche", options=("Material", "Stärke", "Format"), price_mode="tiers", source_filename_token="schweißgitter"),
        "Wellengitter": CategoryConfig("Tafeln", "Wellengitter", "Wellengitter", "Tabelle1", "Maschenweite", "Wellengitter Tafelware", include_definition=False, thickness_column="Drahtstärke", area_column="Ao, ungelochte Fläche", options=("Material", "Stärke", "Format"), price_mode="tiers", source_filename_token="wellengitter"),
    },
    "Zuschnitte": {
        "Lochblech": CategoryConfig("Zuschnitte", "Lochblech", "Lochblech", "Tabelle1", "Lochgröße und -abstand", "Lochblech Zuschnitt", area_column="Ao, gelochte Fläche", source_filename_token="lochblech"),
        "Präge": CategoryConfig("Zuschnitte", "Präge", "Präge", "Tabelle1", "Prägungsgröße und -abstand", "Prägeblech Zuschnitt", include_definition=False, area_column="Geprägte Fläche", source_filename_token="präge"),
        "Glattblech": CategoryConfig("Zuschnitte", "Glattblech", "Glattblech", "qryDatenaustausch_Zuschnitte_Gl", None, "Glattblech Zuschnitt", include_definition=False, area_column="Freie Fläche", source_filename_token="glattblech"),
        "Schweißgitter": CategoryConfig("Zuschnitte", "Schweißgitter", "Schweißgitter", "Tabelle1", "Maschenweite", "Schweißgitter Zuschnitt", include_definition=False, area_column="Freie Fläche", hint_column="Hinweis SG", source_filename_token="schweißgitter"),
        "Wellengitter": CategoryConfig("Zuschnitte", "Wellengitter", "Wellengitter", "Tabelle1", "Maschenweite", "Wellengitter Zuschnitt", include_definition=False, area_column="Freie Fläche", source_filename_token="wellengitter"),
        "Duett": CategoryConfig("Zuschnitte", "Duett", "Duett", "Tabelle1", "Lochgröße und -abstand", "Warzenblech Zuschnitt", include_definition=False, area_column="Geprägte Fläche", source_filename_token="duett"),
        "PVC": CategoryConfig("Zuschnitte", "PVC", "PVC", "Tabelle1", "Lochgröße und -abstand", "PVC Lochplatte Zuschnitt", include_definition=False, area_column="Ao, gelochte Fläche", options=("Farbe", "Material", "Stärke"), source_filename_token="pvc"),
    },
}


def get_category(group: str, category: str) -> CategoryConfig:
    try:
        return CATEGORIES[group][category]
    except KeyError as exc:
        raise ValueError(f"Unknown group/category: {group} / {category}") from exc
