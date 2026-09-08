import { useEffect, useRef, useState } from "react";
import { attachStepMeshes } from "./step-model.mjs";
export default function useStepModel(enabled, url, geometry, retry) {
  const [state, setState] = useState({ status: "idle" }),
    cache = useRef(new Map());
  useEffect(() => {
    if (!enabled || !url || !geometry) return;
    if (cache.current.has(url)) {
      setState(cache.current.get(url));
      return;
    }
    let active = true;
    const worker = new Worker(new URL("./step-worker.js", import.meta.url));
    const timer = setTimeout(() => {
      worker.terminate();
      if (active)
        setState({
          status: "error",
          url,
          error:
            "STEP import exceeded two minutes. Download the file or retry.",
        });
    }, 120000);
    setState({ status: "loading", url, stage: "Starting STEP reader" });
    const fail = (error) => {
      clearTimeout(timer);
      worker.terminate();
      if (active) setState({ status: "error", url, error });
    };
    worker.onmessage = ({ data }) => {
      if (!active) return;
      if (data.error) {
        fail(data.error);
        return;
      }
      if (!data.done) {
        setState({ status: "loading", url, stage: data.stage });
        return;
      }
      try {
        const view = {
          status: "ready",
          url,
          ...attachStepMeshes(geometry, data.meshes),
          root: data.root,
          hash: data.hash,
          bytes: data.bytes,
          cached: data.cached,
        };
        clearTimeout(timer);
        worker.terminate();
        cache.current.set(url, view);
        while (cache.current.size > 2)
          cache.current.delete(cache.current.keys().next().value);
        setState(view);
      } catch (error) {
        fail(error.message);
      }
    };
    worker.onerror = (event) => fail(event.message || "STEP reader failed");
    worker.postMessage({
      url: new URL(url, location.href).href,
      base: location.origin,
      bypassCache: retry > 0,
    });
    return () => {
      active = false;
      clearTimeout(timer);
      worker.terminate();
    };
  }, [enabled, url, geometry, retry]);
  return state.url === url ? state : { status: "idle" };
}
