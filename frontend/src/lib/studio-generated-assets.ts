import type { StudioAiJob, StudioAsset } from "./studio-api";

export type GeneratedStudioAsset = {
  id: string;
  sourceJobId: string;
  sourceKind: string;
  prompt: string;
  rank?: number;
  score?: number;
  name?: string;
  url?: string;
  width?: number;
  height?: number;
  usage?: string;
  tags?: string[];
};

export function collectGeneratedAssets(options: {
  aiJobs: StudioAiJob[];
  assets?: StudioAsset[];
}): GeneratedStudioAsset[] {
  const assetMetadata = new Map((options.assets ?? []).map((asset) => [asset.id, asset]));
  const generatedAssets = new Map<string, GeneratedStudioAsset>();

  options.aiJobs
    .filter((job) => job.status === "succeeded")
    .forEach((job) => {
      if (job.resultAsset?.id) {
        generatedAssets.set(job.resultAsset.id, enrichGeneratedAsset({
          id: job.resultAsset.id,
          sourceJobId: job.id,
          sourceKind: job.kind,
          prompt: job.prompt,
        }, assetMetadata.get(job.resultAsset.id)));
      }

      job.candidates.forEach((candidate) => {
        if (!candidate.assetId || generatedAssets.has(candidate.assetId)) return;
        generatedAssets.set(candidate.assetId, enrichGeneratedAsset({
          id: candidate.assetId,
          sourceJobId: job.id,
          sourceKind: job.kind,
          prompt: job.prompt,
          rank: candidate.rank,
          score: candidate.score,
        }, assetMetadata.get(candidate.assetId)));
      });
    });

  return Array.from(generatedAssets.values());
}

function enrichGeneratedAsset(generated: GeneratedStudioAsset, asset?: StudioAsset): GeneratedStudioAsset {
  if (!asset) return generated;
  return {
    ...generated,
    name: asset.name,
    url: asset.url,
    width: asset.metadata.width,
    height: asset.metadata.height,
    usage: asset.metadata.usage,
    tags: asset.metadata.tags,
  };
}
