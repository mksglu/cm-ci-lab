# Writes a LiteLLM proxy config to stdout. The admin key comes from env and is never printed to the log.
import json, os, sys
gw, tenant, dry = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
hdr = {"x-context-mode-key": os.environ["CM_ADMIN_KEY"], "x-cm-tenant": tenant}
if dry: hdr["x-cm-dry-run"] = "1"
cfg = {
  "model_list": [{"model_name": "*", "litellm_params": {"model": "anthropic/*", "api_base": gw,
                  "api_key": "os.environ/LAB_UPSTREAM_KEY", "extra_headers": hdr}}],
  "general_settings": {"master_key": os.environ["LITELLM_MASTER"], "forward_client_headers_to_llm_api": False},
  "litellm_settings": {"drop_params": False},
}
print(json.dumps(cfg))
