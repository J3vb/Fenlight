# Co-op messages and shared state

Patterns and reference files: `docs/MULTIPLAYER.md` "Writing co-op code".

1. **Handler order.** `is_server()` check, then sender from
   `multiplayer.get_remote_sender_id()` (never from an argument), then
   checks (alive, in range, not too fast, facts true), then reject with a
   rate-limited `Log.warn`, then the same function solo runs.
2. **Client sends only what it owns.** Does the server look up prices,
   damage and other players' facts itself? Is every argument checked:
   NodePath to an unexpected node, index out of range, negative amount,
   unknown content id?
3. **RPC mode.** `any_peer` only on request handlers; server-to-client state
   is `authority`. With `call_remote` / `call_local`, is the change applied
   exactly once on the server, the host player and each client: not zero
   times, not twice?
4. **Reliable or not.** Gameplay state is `reliable`. Only cosmetics are
   `unreliable`, and losing one changes nothing.
5. **Late joiner.** Is the new state in the snapshot a joining client asks
   for? Joining mid-round, mid-vote or while someone is downed shows the truth?
6. **Leaver.** A peer leaves mid-request, mid-revive or with a grant not yet
   acked: is pending state cleared, the vote recounted, the node freed once?
7. **Three ways to run.** Solo (offline peer acting as server), host who is
   also a player, dedicated server with no local player. One code path (ADR
   0004); does each still work?
8. **Grants.** Server to one owner with `rpc_id(owner, ...)`, run directly
   when the owner is the server, acked by the owner. Applied twice if sent twice?
9. **Server-owned node under a Player.** `set_multiplayer_authority(1)` in
   `_init()`, added in `Player._ready()`, same name on every peer, asks for
   its state in `_ready()` when not the server.
10. **Nodes on the wire.** Enemies come from `Spawner`. Are node names and
    paths the same on every peer? Can an RPC reach a client before the node
    exists there?
11. **Cosmetic relay.** Does the owner see its own effect once (local copy
    plus relay = twice)? Does the server check the sender before relaying?
12. **Protocol version.** A new, renamed or moved RPC, a changed argument or
    a moved node bumps `Build.PROTOCOL_VERSION`; tests compare to the constant.
13. **Not allowed without a decision record.** Prediction, interpolation
    buffers, lag compensation.
14. **Test.** A two-peer test in `tests/integration/` covers the networked part.
