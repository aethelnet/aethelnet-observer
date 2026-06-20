# Tauri Setup Requirements

## System Dependencies (Fedora Silverblue)

The Tauri build requires the following system libraries:

```bash
sudo dnf install webkit2gtk4.1-devel libsoup3-devel
```

If `webkit2gtk4.1-devel` is not available, try:

```bash
sudo dnf install webkit2gtk*-devel libsoup3-devel
```

## Rust Compilation Issues

Some Tauri commands have been temporarily commented out in `src-tauri/src/lib.rs` due to serialization issues. These can be fixed during migration:

- `fetch_auto_discovery_symbols` - Returns `HashMap<String, AutoDiscoverySymbol>`
- `fetch_auto_discovery_patterns` - Returns `EpisodePatternSummary`
- `promote_symbol_to_whitelist` - Returns `String`
- `remove_discovered_symbol` - Returns `String`
- `update_episode_patterns` - Returns `String`

**Status:** Basic infrastructure commands are enabled and should work once system dependencies are installed.

## Next Steps

1. Install system dependencies (see above)
2. Run `npm run tauri:dev` to test
3. Fix remaining command serialization issues during migration



