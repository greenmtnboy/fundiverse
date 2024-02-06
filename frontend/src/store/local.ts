import Store from "electron-store";

const store = new Store<Record<string, string>>({
  name: "login-encrypted",
  watch: true,
  encryptionKey: "this_is_always_accessible_by_user",
});

export default store;
