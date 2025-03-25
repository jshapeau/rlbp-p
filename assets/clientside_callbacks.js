
if (!window.dash_clientside) window.dash_clientside = {};

if (!window.dash_clientside.bison) window.dash_clientside.bison = {};

window.dash_clientside.bison.toggleCardCollapse = function(n_clicks, is_open) {
    if (!n_clicks) {
        return window.dash_clientside.no_update;
    }
    
    const new_is_open = !is_open;
    const new_button_text = new_is_open ? "-" : "+";
    
    return [new_is_open, new_button_text];
};

window.dash_clientside.bison.toggleSliderCollapse = function(n_clicks, is_open) {
    if (!n_clicks) {
        return window.dash_clientside.no_update;
    }
    
    const new_is_open = !is_open;
    const new_button_text = new_is_open ? "Less Detail" : "More Detail";
    
    return [new_is_open, new_button_text];
};

window.dash_clientside.bison.toggleLegendCollapse = function(n_clicks, is_open) {
    if (!n_clicks) {
        return window.dash_clientside.no_update;
    }
    
    // Toggle the collapse state
    const newState = !is_open;
    
    // Find the category element that was clicked
    const categoryId = window.dash_clientside.callback_context.triggered[0]['prop_id'].split('.')[0];
    
    // Find the associated toggle element
    const toggleId = "toggle-" + categoryId.substring("category-".length);
    const toggleElement = document.getElementById(toggleId);
    
    // Update the toggle text based on the new state
    if (toggleElement) {
        toggleElement.innerText = newState ? "-" : "+";
    }
    
    return newState;
};