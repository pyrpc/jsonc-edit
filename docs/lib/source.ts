import { toFumadocsSource } from 'fumadocs-mdx/runtime/server';
import { loader } from 'fumadocs-core/source';
import { docs, meta } from '@/.source/server';

export const source = loader({
  baseUrl: '/docs',
  source: toFumadocsSource(docs, meta),
});
