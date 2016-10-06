#include "fonts.h"
#include "format.h"
#include "layout.h"
#include "preferences.h"
#include "staleness.h"
#include "status_bar_element.h"

StatusBarElement* status_bar_element_create(Layer *parent) {
  GRect bounds = element_get_bounds(parent);

  int sm_text_margin = 2;
  FontChoice font = get_font(FONT_18_BOLD);

  int text_y, height;
  if (bounds.size.h <= font.height * 2 + font.padding_top + font.padding_bottom) {
    // vertically center text if there is only room for one line
    text_y = (bounds.size.h - font.height) / 2 - font.padding_top;
    height = font.height + font.padding_top + font.padding_bottom;
  } else {
    // otherwise take up all the space, with half the default padding
    text_y = -1 * font.padding_top / 2;
    height = bounds.size.h - text_y;
  }

  TextLayer *text = text_layer_create(GRect(
    sm_text_margin,
    text_y,
    bounds.size.w - sm_text_margin,
    height
  ));
  text_layer_set_text_alignment(text, GTextAlignmentLeft);
  text_layer_set_background_color(text, GColorClear);
  text_layer_set_text_color(text, element_fg(parent));

  text_layer_set_font(text, fonts_get_system_font(font.key));
  text_layer_set_overflow_mode(text, GTextOverflowModeWordWrap);
  layer_add_child(parent, text_layer_get_layer(text));

  BatteryComponent *battery = NULL;
  if (get_prefs()->battery_loc == BATTERY_LOC_STATUS_RIGHT) {
    // align the battery to the middle of the lowest line of text
    int lines = (bounds.size.h - text_y) / (font.height + font.padding_top);
    int battery_y = text_y + (font.height + font.padding_top) * (lines - 1) + font.padding_top + font.height / 2 - battery_component_height() / 2;
    // ...unless that places it too close to the bottom
    if (battery_y + battery_component_height() - battery_component_vertical_padding() > bounds.size.h - sm_text_margin) {
      battery_y = bounds.size.h - battery_component_height() + battery_component_vertical_padding() - sm_text_margin;
    }

    battery = battery_component_create(parent, bounds.size.w - battery_component_width() - sm_text_margin, battery_y, true);
  }

  RecencyComponent* recency = NULL;
  if (get_prefs()->recency_loc == RECENCY_LOC_STATUS_TOP_RIGHT || get_prefs()->recency_loc == RECENCY_LOC_STATUS_BOTTOM_RIGHT) {
    int lines;
    if (get_prefs()->recency_loc == RECENCY_LOC_STATUS_TOP_RIGHT) {
      lines = 1;
    } else {
      lines = (bounds.size.h - text_y) / (font.height + font.padding_top);
    }
    // vertically align with the center of the first/last line of text
    int16_t recency_y = text_y + (font.height + font.padding_top) * (lines - 1) + font.padding_top + font.height / 2 - recency_component_size() / 2;
    // keep it within the bounds
    if (recency_y + recency_component_padding() < 0) {
      recency_y = -recency_component_padding();
    } else if (recency_y + recency_component_size() > bounds.size.h) {
      recency_y = bounds.size.h - recency_component_size() + recency_component_padding();
    }

    recency = recency_component_create(parent, recency_y, true, NULL, NULL);
  }

  StatusBarElement *el = malloc(sizeof(StatusBarElement));
  el->text = text;
  el->battery = battery;
  el->recency = recency;
  return el;
}

void status_bar_element_destroy(StatusBarElement *el) {
  text_layer_destroy(el->text);
  if (el->battery != NULL) {
    battery_component_destroy(el->battery);
  }
  if (el->recency != NULL) {
    recency_component_destroy(el->recency);
  }
  free(el);
}

void status_bar_element_update(StatusBarElement *el, DataMessage *data) {
  status_bar_element_tick(el);
}

void status_bar_element_tick(StatusBarElement *el) {
  if (last_data_message() == NULL) {
    return;
  }
  static char buffer[STATUS_BAR_MAX_LENGTH + 16];
  format_status_bar_text(buffer, sizeof(buffer), last_data_message());
  text_layer_set_text(el->text, buffer);

  if (el->recency != NULL) {
    recency_component_tick(el->recency);
  }
}
