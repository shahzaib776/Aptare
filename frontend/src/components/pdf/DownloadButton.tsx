interface Props {
  /** The hash of the PDF on screen; the button saves exactly that stored file (EX-2). */
  pdfHash: string | undefined;
  /** A newer render is on its way, so what is on screen is about to change (EX-3). */
  pending: boolean;
}

export function DownloadButton({ pdfHash, pending }: Props) {
  function save() {
    if (!pdfHash) return;
    // The server marks the file "inline", which a browser would open in a tab; the download
    // attribute makes it save instead. The link is clicked, not fetched, so no copy is made.
    const link = document.createElement("a");
    link.href = `/api/v1/files/pdf/${pdfHash}`;
    link.download = "resume.pdf";
    document.body.append(link);
    link.click();
    link.remove();
  }

  return (
    <button
      type="button"
      disabled={pending || !pdfHash}
      onClick={save}
      className="min-h-11 rounded bg-slate-900 px-4 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
    >
      Download PDF
    </button>
  );
}
