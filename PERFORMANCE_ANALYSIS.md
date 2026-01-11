# Performance Analysis

## Current Bottlenecks

### 1. **Serial Processing** (Most Critical)
**Location**: `discover_links_recursive()` and `run()`

**Problem**:
- Pages are visited one at a time
- Only uses a single browser page/tab
- No concurrent processing

**Impact**:
- For 100 pages with 2s average load time = 200 seconds
- Network I/O bound operation running sequentially

**Measurement**:
```python
# Current: ~2-3 seconds per page
# 100 pages = 200-300 seconds (~3-5 minutes)
```

### 2. **Expensive Page Waits**
**Location**: Line 175 in `discover_links_recursive()`

**Problem**:
```python
page.wait_for_load_state('networkidle', timeout=15000)
```
- Waits for ALL network requests to finish
- Many documentation sites have analytics/tracking that delay networkidle
- 15 second timeout is very long

**Impact**:
- Can add 5-10 seconds per page unnecessarily
- Blocks other operations while waiting

### 3. **No Browser Reuse During Crawling**
**Location**: `run()` method

**Problem**:
- Creates new browser instance for crawling even if just did discovery
- Browser startup overhead (~1-2 seconds)

### 4. **Redundant Page Visits**
**Location**: Both discovery and crawling phases

**Problem**:
- Discovery visits pages to extract links
- Crawling visits same pages again to extract content
- Each page visited twice!

**Impact**:
- 2x network requests
- 2x page load time

### 5. **Memory Usage**
**Problem**:
- All results stored in memory before writing
- For large sites (1000+ pages), this could be significant

## Optimization Opportunities

### High Impact (Easy Wins)

#### 1. Concurrent Page Loading
**Estimated Speedup**: 10-20x for I/O bound operations

```python
# Current: Serial
for url in urls:
    visit(url)

# Optimized: Parallel with 10 workers
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(visit, url) for url in urls]
```

**Implementation**:
- Use multiple browser contexts/pages
- Process 5-10 pages concurrently
- Respect rate limiting

#### 2. Smart Waiting Strategy
**Estimated Speedup**: 2-3x

```python
# Instead of networkidle (slow):
page.wait_for_load_state('networkidle', timeout=15000)

# Use domcontentloaded (faster):
page.wait_for_load_state('domcontentloaded', timeout=5000)
# Then wait for specific selector
page.wait_for_selector('article, main', timeout=5000)
```

#### 3. Combined Discovery + Crawling
**Estimated Speedup**: 2x

Extract content during discovery phase instead of visiting twice:
```python
def discover_and_crawl(url):
    page.goto(url)
    links = extract_links(page)  # Discovery
    content = extract_content(page)  # Crawling
    return links, content
```

### Medium Impact

#### 4. Async/Await with Playwright Async API
**Estimated Speedup**: 15-30x for large crawls

```python
# Use playwright's async API
from playwright.async_api import async_playwright

async def crawl_concurrent(urls, max_concurrent=10):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_one(url):
            async with semaphore:
                page = await browser.new_page()
                await page.goto(url)
                # ... extract content
                await page.close()

        await asyncio.gather(*[crawl_one(url) for url in urls])
```

#### 5. Intelligent Depth-First vs Breadth-First
**Current**: Uses set.pop() which is unordered
**Better**: Use deque for BFS to find all links faster

```python
from collections import deque

# BFS finds more links faster
to_visit = deque([start_url])
while to_visit:
    current = to_visit.popleft()  # FIFO
```

#### 6. Early Termination
Stop discovery once we have enough URLs:
```python
if len(discovered) >= desired_count:
    break
```

### Low Impact (Nice to Have)

#### 7. Response Caching
Cache responses to avoid re-fetching:
```python
@lru_cache(maxsize=1000)
def fetch_page(url):
    ...
```

#### 8. Streaming Output
Write results as they're generated instead of buffering:
```python
# Instead of storing all in memory
with open(output, 'w') as f:
    for result in process_urls(urls):
        f.write(result)
```

## Recommended Implementation Priority

### Phase 1: Quick Wins (Implement First)
1. ✅ Combined discovery + crawling (avoid double visit)
2. ✅ Smart waiting strategy (domcontentloaded instead of networkidle)
3. ✅ Concurrent page loading (5-10 workers with ThreadPoolExecutor)

**Expected**: 10-20x speedup, 100 pages in 10-20 seconds instead of 3-5 minutes

### Phase 2: Major Refactor (Optional)
4. Async/await implementation
5. Better memory management

**Expected**: Additional 2-3x speedup

### Phase 3: Polish
6. Caching
7. Rate limiting
8. Progress persistence

## Testing Requirements

Need tests for:
1. ✅ Link extraction accuracy
2. ✅ Content conversion quality
3. ✅ Concurrent safety (no race conditions)
4. ✅ Error handling under concurrent load
5. ✅ Memory usage monitoring
6. ✅ Performance benchmarks

## Benchmarking Plan

Create synthetic test scenarios:
- Small site: 10 pages
- Medium site: 50 pages
- Large site: 200 pages

Measure:
- Total time
- Pages per second
- Memory usage
- Error rate

Current baseline (estimated):
- Small: 20-30 seconds
- Medium: 100-150 seconds
- Large: 400-600 seconds

Target with optimizations:
- Small: 3-5 seconds (6x improvement)
- Medium: 8-12 seconds (12x improvement)
- Large: 20-40 seconds (15x improvement)
