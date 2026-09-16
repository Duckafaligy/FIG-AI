"use client";

import { useId, useRef } from "react";
import { X } from "lucide-react";

export function PreviewInfo({ label, message, className = "text-button" }: { label: string; message: string; className?: string }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  return <>
    <button type="button" className={className} onClick={() => dialog.current?.showModal()}>{label}</button>
    <dialog ref={dialog} className="preview-info-dialog" aria-labelledby={titleId} onClick={(event) => { if (event.target === event.currentTarget) dialog.current?.close(); }}>
      <div><h2 id={titleId}>{label}</h2><button type="button" aria-label="Close" onClick={() => dialog.current?.close()}><X size={19} /></button></div>
      <p>{message}</p>
      <button className="button" type="button" onClick={() => dialog.current?.close()}>Got it</button>
    </dialog>
  </>;
}
