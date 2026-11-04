// Pentair ConnectMySoftener: loads the dashboard card bundled with the integration,
// unless the card is already installed as a Lovelace resource (then the user's own,
// possibly newer, copy wins and we must not shadow it with ours).
const version = new URL(import.meta.url).searchParams.get("v") || "0";
const bundle = `/pentair_softener/pentair-softener-card.js?v=${version}`;

async function cardResourcePresent() {
  try {
    const { conn } = await window.hassConnection;
    const resources = await conn.sendMessagePromise({ type: "lovelace/resources" });
    return resources.some((r) => String(r.url).includes("pentair-softener-card"));
  } catch (err) {
    // no connection yet, or no right to list resources (non-admin): load the bundled card
    return false;
  }
}

if (customElements.get("pentair-softener-card")) {
  console.info("Pentair ConnectMySoftener: card already loaded");
} else if (await cardResourcePresent()) {
  console.info("Pentair ConnectMySoftener: using the card from a Lovelace resource");
} else {
  await import(bundle);
}
