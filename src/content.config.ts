import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
const candies = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/candies' }),
  schema: z.object({
    title: z.string(), brand: z.string(), line: z.string().default(''),
    flavors: z.array(z.string()).default([]), collection: z.string().default(''),
    date: z.coerce.date(), photos: z.array(z.string()).default([]),
  }),
});
export const collections = { candies };
