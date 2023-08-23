from dash import dcc
import dash_bootstrap_components as dbc

color_palette: dict[str, str] = {
    "dark_blue": "#06283D",
    "medium_blue": "#1363DF",
    "light_blue": "#47B5FF",
    "off_white": "#DFF6FF"
}
def get_card(children, id=None, style=None, className=None):
    """
    Generates a styled Card component using the Dash Bootstrap Components library.

    :param children: content to be placed inside the card's bod
    :param id: identifier for the card
    :param style: dictionary containing CSS properties to style the card
    :return:
    """
    default_style = {
        'backgroundColor': color_palette['off_white'],
        'border': '1px solid ' + color_palette['medium_blue'],
        'boxShadow': '3px 3px 5px ' + color_palette['light_blue'],
        'color': color_palette['dark_blue']
    }

    # If any custom styles are provided, they should override the default styles.
    if style:
        default_style.update(style)

    return dbc.Card(
        dbc.CardBody(children),
        style=default_style,
        className = className
    )


def get_badge(text, id=None):
    """
    Generates a styled Badge component using the Dash Bootstrap Components library.

    :param text: text to be placed inside the badge
    :param id: identifier for the card
    :return:
    """
    return dbc.Badge(text, id=id, style={
        'backgroundColor': color_palette['medium_blue'],
        'border': 'none',
        'color': color_palette['off_white'],
    })