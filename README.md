# State-Aware Bourbon Allocation Hunting System

This package adds intelligent state-aware retail system recognition to Sam, your bourbon allocation hunting agent.

## Problem Solved

Your current Sam implementation was filtering out legitimate allocation stores in Seattle (and other chain-friendly markets) because it excluded all chain stores. This left you with 0 results and generic placeholder text.

**The issue:** Different states have completely different liquor retail systems:
- **Kentucky/Tennessee** → Independent liquor stores dominate
- **Washington/California** → Major chains (Total Wine, BevMo) handle allocations
- **Pennsylvania/Virginia** → State-run ABC stores control everything

Sam now understands these differences and adapts its search and filtering accordingly.

## What's Included

### 1. `state_retail_systems.py`
Configuration file that categorizes all 50 US states into three retail system types:

- **Independent Dominant** (24 states): KY, TN, TX, GA, FL, etc.
  - Strategy: Build relationships with local shop owners
  - Filters: Exclude all chains, focus on independent stores

- **Chain Friendly** (10 states): WA, CA, AZ, NV, CO, IL, etc.
  - Strategy: Check chain lotteries + specialty retailers
  - Filters: Allow approved allocation chains (Total Wine, BevMo, etc.)

- **State Controlled** (14 states): PA, NC, VA, OR, UT, etc.
  - Strategy: Monitor state ABC websites for lottery systems
  - Filters: Look for government stores and state liquor outlets

### 2. `store_filters.py`
Smart filtering logic that adapts based on state retail system:

- `filter_stores_by_state_system()` - Main filtering function
- `build_search_query()` - Generates state-appropriate search queries
- `enhance_places_with_allocation_likelihood()` - Scores stores by allocation probability

### 3. `test_state_systems.py`
Comprehensive test suite to verify everything works:

```bash
python test_state_systems.py
```

Tests include:
- State classification (50 states)
- Chain filtering logic
- Search query generation
- Hunt plan creation
- Store filtering with mock data
- Response formatting

### 4. `INTEGRATION_GUIDE.md`
Step-by-step instructions for integrating into your `sam_engine.py`.

## Quick Start

1. **Copy files to your sam-agent backend:**
   ```bash
   cp state_retail_systems.py /path/to/sam-agent/
   cp store_filters.py /path/to/sam-agent/
   ```

2. **Run tests to verify:**
   ```bash
   python test_state_systems.py
   ```

3. **Follow the integration guide:**
   - Update imports in `sam_engine.py`
   - Replace `_hunt_plan()` method
   - Update `_search_allocation_stores()` method
   - Test with different states

## Example Output Differences

### Before (Seattle, WA):
```
Allocation stores in seattle, washington.

Step 1 - Local Liquor Store
Near seattle, washington
Call and ask about allocation process.
```
*Result: 0 stores found (all filtered out)*

### After (Seattle, WA):
```
**Bourbon allocation hunting in Seattle, WA**

**Market Type:** Chain-Inclusive Market
Private retail market where major chains and specialty retailers 
handle significant allocation volume alongside independent stores.

**Best Strategy:** Check both major chains (Total Wine, BevMo) and 
independent specialty shops. Many chains use lottery or waitlist systems.

**Stores to check:**
1. **Total Wine & More**
   1205 4th Ave, Seattle, WA 98161

2. **McCarthy & Schiering Wine Merchants**
   2401 Queen Anne Ave N, Seattle, WA 98109

3. **BevMo**
   1151 N 205th St, Shoreline, WA 98133

**Hunting Steps:**

**Step 1: Check Major Chain Lotteries**
Visit Total Wine, BevMo websites and sign up for allocation lotteries
*Tip: Some chains require in-store signup - call to confirm*

**Step 2: Find Specialty Retailers**
Search for independent liquor stores known for good bourbon selection
*Tip: Check local bourbon Facebook groups for recommendations*
...
```
*Result: 8+ relevant stores with specific guidance*

## Key Features

### Intelligent Filtering
- **Kentucky**: Excludes all chains → focuses on local relationships
- **Washington**: Includes Total Wine/BevMo → suggests lottery signup
- **Pennsylvania**: Shows ABC stores → links to state website

### State-Specific Guidance
Each hunt plan includes:
- Market type explanation
- Allocation strategy for that state
- Appropriate hunting steps
- State ABC website (for controlled states)

### Extensible Design
- Easy to add new states
- Simple to adjust approved/excluded chains
- Clear configuration structure
- Comprehensive documentation

## State Coverage

### ✅ Currently Supported: All 50 States

**Independent Markets (24):** KY, TN, TX, GA, FL, IN, OH, MI, NY, NJ, SC, OK, KS, NE, SD, ND, IA, MN, AR, CT, DE, MA, RI, MD

**Chain-Friendly (10):** WA, CA, AZ, NV, CO, NM, LA, MO, WI, IL

**State-Controlled (14):** PA, UT, NC, VA, AL, ID, NH, MS, MT, OR, VT, WY, WV, ME

## Configuration Details

### Approved Allocation Chains (Chain-Friendly States)
- Total Wine & More
- BevMo
- Binny's (IL)
- K&L Wine Merchants (CA)
- Spec's (TX)
- Twin Liquors (TX)
- Hi-Time Wine Cellars (CA)
- Mission Liquor (CA)

### Always Excluded Chains (All States)
- Walmart
- Target
- Costco
- Kroger
- Safeway
- Whole Foods
- Trader Joe's
- Fred Meyer

## Technical Details

### Dependencies
- Python 3.7+
- No additional packages required (uses only standard library)

### Integration Points
- Replaces: Generic store filtering in `_hunt_plan()`
- Adds: State classification before search
- Updates: Search query building
- Enhances: Response formatting with state context

### Debug Mode
Enable detailed logging to see filtering decisions:
```python
filtered_stores = filter_stores_by_state_system(places, "WA", debug=True)
```

Output:
```
DEBUG: Filtering for WA using 'selective_chain' strategy
DEBUG: ✓ Including 'Total Wine & More' - approved allocation chain
DEBUG: Skipping 'Fred Meyer' - excluded chain
DEBUG: ✓ Including 'McCarthy & Schiering' - liquor store
```

## Testing Your Integration

After integrating, test with these representative cities:

```python
# Test independent market
engine._hunt_plan(session, "Louisville", "KY")

# Test chain-friendly market
engine._hunt_plan(session, "Seattle", "WA")

# Test state-controlled market
engine._hunt_plan(session, "Philadelphia", "PA")
```

Expected results:
- KY: Only independent stores, relationship-building advice
- WA: Mix of chains + independents, lottery system guidance
- PA: ABC stores, state website link, lottery instructions

## Troubleshooting

### "Still getting 0 stores for Seattle"
1. Verify `state_retail_systems.py` is imported
2. Check state abbreviation is uppercase: "WA" not "wa"
3. Enable debug mode to see filtering decisions
4. Verify Google Places API is returning results

### "Wrong stores showing up"
1. Check the `approved_chains` list for your state
2. Adjust `exclude_chains` if needed
3. Review debug output to see which filters applied
4. Consider if store should be in approved list

### "State-controlled market not working"
1. Verify state is in `state_controlled` states list
2. Check `state_specific_terms` for that state
3. Some states may need custom search queries
4. Review state ABC website URL in config

## Future Enhancements

Potential additions:
- User feedback system ("Was this helpful?")
- Store verification through Brave Search
- Real-time allocation drop notifications
- State-specific holiday release schedules
- Store rating/ranking based on user reports
- Integration with bourbon secondary market data

## Support

If you encounter issues:
1. Run `test_state_systems.py` to verify configuration
2. Enable debug mode to see filtering decisions
3. Check your state classification in `STATE_RETAIL_SYSTEMS`
4. Review the integration guide for common mistakes

## Version History

**v1.0** (January 2026)
- Initial release
- 50 state coverage
- Three retail system types
- Comprehensive filtering logic
- Full test suite
- Integration documentation

---

Built for Sam, your bourbon allocation hunting companion 🥃
