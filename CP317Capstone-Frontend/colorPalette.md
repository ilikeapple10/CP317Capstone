# Color Palette: Product Search

Each color has one job. When adding a new color, make it take over one of these jobs rather than adding a new one. (this will probably change by sprint 2)

## Colors by job

| Job | Color | Hex | Used on |
|---|---|---|---|
| Action color | Blue | `#2563eb` | Buttons and anything clickable, plus the focus outline on inputs |
| Action hover | Darker blue | `#1d4ed8` | Button on hover |
| Action pressed | Darkest blue | `#1e40af` | Button while clicked |
| Header | Dark navy | `#131921` | The top bar only |
| Page background | Light gray | `#f4f6fb` | Behind everything |
| Card background | White | `#ffffff` | Cards, search box and dropdown fill |
| Main text | Dark gray | `#1f2937` | Titles, product names, prices |
| Secondary text | Mid gray | `#6b7280` | Subtitles, column headings, category names, "6 results" |
| Input border | Light gray | `#d1d5db` | Search box and dropdown outline |
| Table border | Lighter gray | `#e5e7eb` | Table outline, header underline, thumbnail border |
| Row divider | Faint gray | `#f0f1f4` | Thin line between table rows |
| Table header fill | Off-white | `#f9fafb` | PRODUCT / PRICE / STATUS row background |
| Row hover | Faint blue | `#f8faff` | Table row when the mouse is over it |
| Highlight | Orange | `#febd69` | Cart count badge only |

## Status colors (reserved for stock status and errors)

| Meaning | Text | Background |
|---|---|---|
| In stock (green) | `#166534` | `#dcfce7` |
| Low stock (amber) | `#92400e` | `#fef3c7` |
| Out of stock / error (red) | `#991b1b` | `#fee2e2` |

## Image tiles

| Job | Hex | Used on |
|---|---|---|
| Photo background | `#f3f4f6` | Behind a product photo while it loads |
| Placeholder fill | `#e0e9ff` | Lettered tile when there is no photo |
| Placeholder border | `#c7d6fe` | Outline of that tile |
| Placeholder letter | `#2563eb` | The letter on the tile |

## Rules for adding new colors

- **A new card color** replaces the white card background. Keep the page background slightly darker so cards stand out.
- **A new text color** replaces main or secondary text. Main text stays the darkest color on the page.
- **A new button color** replaces the action blue everywhere, so all buttons match.
- **A new accent color** (like the orange) is for one small highlight, never large areas.
- **Green, amber and red** are reserved for status and errors, not decoration.
- Text on the dark header stays white.
