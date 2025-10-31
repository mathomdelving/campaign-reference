'use client';

import { useRef } from "react";
import { ShareCard, type ShareCardProps } from "@/components/ShareCard";
import { exportNodeToPng } from "@/lib/export";

export interface SharePreviewProps extends ShareCardProps {
  fileName?: string;
}

export function SharePreview({
  fileName = "campaign-reference-share.png",
  ...props
}: SharePreviewProps) {
  const captureRef = useRef<HTMLDivElement>(null);

  const handleDownload = async () => {
    if (!captureRef.current) return;
    await exportNodeToPng(captureRef.current, { fileName });
  };

  return (
    <div className="space-y-8">
      <div
        ref={captureRef}
        className="mx-auto w-[1200px] overflow-visible rounded-[32px]"
      >
        <ShareCard {...props} />
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleDownload}
          className="inline-flex items-center gap-3 rounded-full border border-rb-yellow/40 bg-rb-red/90 px-6 py-3 text-sm font-semibold uppercase tracking-[0.3rem] text-white transition hover:bg-rb-red hover:shadow-lg hover:shadow-rb-red/30"
        >
          Download PNG
        </button>
      </div>
    </div>
  );
}
