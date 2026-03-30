import "vuetify/styles";

// Vuetify
import type { FunctionalComponent } from "vue";
import { createVuetify } from "vuetify";
import { h } from "vue";
import * as mdiIcons from "@mdi/js";
import { aliases as mdiSvgAliases, mdi as mdiSvg } from "vuetify/iconsets/mdi-svg";
import { VSvgIcon } from "vuetify/lib/composables/icons.mjs";

function toMdiExportName(iconName: string): string {
  return iconName.replace(/-([a-z0-9])/g, (_, char: string) => char.toUpperCase());
}

const MdiSvgIcon: FunctionalComponent<any> = (props) => {
  const iconName = typeof props.icon === "string" ? props.icon.trim() : undefined;
    const iconPath =
      iconName && iconName in mdiIcons
        ? (mdiIcons as Record<string, string>)[iconName]
        : iconName
          ? (mdiIcons as Record<string, string>)[toMdiExportName(iconName)]
          : undefined;

  if (!iconPath) {
    return h(props.tag, { class: "v-icon__missing" });
  }

  return h(VSvgIcon, {
    ...props,
    icon: iconPath,
  });
};

const mdi = {
  component: MdiSvgIcon,
};

export default createVuetify({
  icons: {
    defaultSet: "mdi",
    aliases: mdiSvgAliases,
    sets: {
      mdi,
      svg: mdiSvg,
    },
  },
});
// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
