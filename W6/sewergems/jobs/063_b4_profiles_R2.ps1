. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$log = New-Object IO.StringWriter
function Dump($obj, $title, $max) {
  $log.WriteLine("== $title : " + $obj.GetType().FullName); $k = 0
  foreach ($mi in ($obj.GetType().GetMembers() | Sort-Object Name)) {
    if ($mi.MemberType -eq 'Method' -and $mi.Name -match '^(get_|set_|add_|remove_)') { continue }
    if ($mi.DeclaringType -eq [object]) { continue }
    $sig = ''; if ($mi.MemberType -eq 'Method') { $sig = '(' + (($mi.GetParameters() | ForEach-Object { $_.ParameterType.Name + ' ' + $_.Name }) -join ', ') + ') : ' + $mi.ReturnType.Name } elseif ($mi.MemberType -eq 'Property') { $sig = ' : ' + $mi.PropertyType.Name }
    $log.WriteLine('   ' + $mi.MemberType + ' ' + $mi.Name + $sig); $k++; if ($k -ge $max) { $log.WriteLine('   ...'); break }
  }
}
function MakeProfile($pm, $label, $path) {
  $labelF = $pm.SelectionSetField('Label'); $idsF = $pm.SelectionSetField('SelectionSetElementIDs')
  $existing = @($pm.Elements() | Where-Object { $_.Label -eq $label })
  foreach ($e in $existing) { $pm.Delete($e.Id); $log.WriteLine('  replaced the existing profile "' + $label + '" (' + $e.Id + ')') }
  $new = $pm.Add(); $labelF.SetValue($new, $label)
  $coll = New-Object Haestad.Support.Support.HmIDCollection
  foreach ($i in $path) { [void]$coll.Add([int]$i) }
  $idsF.SetValue($new, $coll)
  $b = @(); foreach ($i in $idsF.GetValue($new)) { $b += [int]$i }
  $log.WriteLine('  profile ' + $new + ' "' + $labelF.GetValue($new) + '": ' + $b.Count + ' elements')
  return $new
}

# Block 04 (engineer, 2026-10-11): the 37 channel profiles, named as the channels of "Channels and Dykes 04102026", written into
# a NEW revision: R2 = the computed R1 of the 17:21 run (designed sizes of all eight scenarios) + the profiles. Each profile is a
# selection set under ProfileManager holding the channel's nodes and conduits from the start to the junction point on the receiving
# channel or the outfall. Delivered to the share: R2 .stsw + .sqlite, the result files of the eight scenarios renamed for R2, and
# the engineer's .dwh and .profiles.dwh copied under the R2 name so the drawing and profile settings travel with it. The 43 profiles
# inherited from the Rustaq model (their elements do not exist here) are left in place for the engineer to delete.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$work = 'C:\B4Work\run_20261011_1721'
$src = "$work\SewerGEMS Block 04_R1.stsw"; $dst = "$work\SewerGEMS Block 04_R2.stsw"
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $pm = $m.DomainDataSet.ProfileManager
  $log.WriteLine('profiles before: ' + @($pm.Elements()).Count)
  [void](MakeProfile $pm 'HAW-CH1-FP' @(1580, 1942, 1691, 2007, 1730, 1840, 1741, 2014, 1752, 1809, 1763, 1821, 1774, 1953, 2023))
  [void](MakeProfile $pm 'HAW-CH2-SS' @(1796, 1979, 1581, 1944, 1592, 1915, 1603, 1832, 1614, 2005, 1625, 1892, 1636, 1815, 1647, 1856, 1774))
  [void](MakeProfile $pm 'HAW-CH3-SS' @(1658, 1977, 1581))
  [void](MakeProfile $pm 'HAW-CH4-SS' @(1669, 1894, 1680, 1862, 1703))
  [void](MakeProfile $pm 'HAW-CH5-SS' @(1692, 1960, 1703, 1914, 1714, 1933, 1723, 1827, 1724, 1992, 1725, 1969, 1726, 1813, 1763))
  [void](MakeProfile $pm 'HAW-CH6-SS' @(1727, 1968, 1636))
  [void](MakeProfile $pm 'HAW-CH7-SS' @(1728, 1962, 1729, 1846, 1731, 1957, 1732, 1980, 1733, 1863, 1734, 1956, 2027))
  [void](MakeProfile $pm 'SAK-CH1-FP' @(1736, 1871, 1737, 1824, 1738, 1913, 1739, 1925, 1740, 1971, 1742, 2000, 1743, 1954, 1744, 1941, 1745, 1889, 1746, 1948, 1747, 1967, 1748, 1906, 1753))
  [void](MakeProfile $pm 'SAK-CH2-FP' @(1749, 1916, 1750, 1978, 1751, 1898, 1753, 2002, 1754, 2013, 1755, 1958, 1756, 1934, 2026))
  [void](MakeProfile $pm 'SAK-CH3-SM' @(1758, 1999, 1759, 1998, 1760, 1872, 1761, 1861, 1762, 1920, 1764, 1816, 2025))
  [void](MakeProfile $pm 'SAK-CH4-SS' @(1766, 1973, 1767, 1857, 1759))
  [void](MakeProfile $pm 'SAK-CH5-SS' @(1768, 1986, 1769, 1943, 2024))
  [void](MakeProfile $pm 'SAR-CH1-FP' @(1771, 1897, 1772, 1972, 1773, 1927, 1775, 2001, 1776, 2016, 1777, 2004, 1778, 1989, 1779, 1893, 1780, 1935, 1781, 1884, 1782, 1947, 1783, 1853, 1784, 1982, 1786, 1810, 2022))
  [void](MakeProfile $pm 'SAR-CH2-SM' @(1788, 1879, 1789, 1938, 1790, 1845, 1791, 1903, 1792, 1826, 1793, 2011, 2021))
  [void](MakeProfile $pm 'SAR-CH3-SS' @(1795, 2017, 1797, 1895, 1798, 2008, 1799, 1919, 1777))
  [void](MakeProfile $pm 'SAR-CH4-SS' @(1800, 2012, 1801, 1883, 1784))
  [void](MakeProfile $pm 'SHA-CH1-FP' @(1802, 1885, 1803, 1858, 1804, 1866, 1805, 1949, 1806, 1843, 1582, 1926, 1583, 1817, 1584, 1814, 1585, 1819, 1586, 1932, 1587, 1836, 1588, 1918, 2034))
  [void](MakeProfile $pm 'SHA-CH10-SS' @(1667, 2003, 1668, 1929, 1670, 1899, 1671, 1931, 1672, 1859, 1628))
  [void](MakeProfile $pm 'SHA-CH11-SS' @(1673, 1974, 1674, 1937, 1632))
  [void](MakeProfile $pm 'SHA-CH12-SS' @(1675, 1869, 1676, 1900, 1677, 1939, 1678, 1847, 1679, 1887, 1606))
  [void](MakeProfile $pm 'SHA-CH13-SS' @(1681, 1984, 1682))
  [void](MakeProfile $pm 'SHA-CH14-SS' @(1683, 1994, 1684, 1849, 1685, 1833, 1686, 1917, 1612))
  [void](MakeProfile $pm 'SHA-CH15-SS' @(1687, 1907, 1688, 1875, 1689, 1911, 1690, 1855, 1693, 1834, 1694, 1951, 1695, 1873, 1696, 1955, 1616))
  [void](MakeProfile $pm 'SHA-CH16-SS' @(1697, 1981, 1698, 1835, 1699, 1877, 1700, 1928, 1701, 1839, 1702, 1995, 1704, 1811, 2029))
  [void](MakeProfile $pm 'SHA-CH17-SS' @(1706, 1993, 1707, 1921, 1708, 1841, 1709, 1950, 1710, 1882, 1584))
  [void](MakeProfile $pm 'SHA-CH18-SS' @(1711, 1890, 1712, 1842, 1713, 1848, 1715, 1966, 1585))
  [void](MakeProfile $pm 'SHA-CH19-SS' @(1716, 1991, 2028))
  [void](MakeProfile $pm 'SHA-CH2-SM' @(1590, 1987, 1591, 1970, 1593, 1924, 1594, 2010, 1595, 2015, 1596, 1844, 1597, 1876, 1598, 1961, 1782))
  [void](MakeProfile $pm 'SHA-CH20-SS' @(1718, 1912, 1719, 1964, 1720, 1940, 1721, 1865, 1587))
  [void](MakeProfile $pm 'SHA-CH21-SS' @(1722, 1946, 1645))
  [void](MakeProfile $pm 'SHA-CH3-SM' @(1599, 1905, 1600, 1886, 1601, 1850, 1602, 1997, 1604, 1988, 1605, 2006, 1606, 1825, 1607, 1837, 1608, 1963, 1609, 1830, 1610, 1828, 1611, 1909, 1612, 1822, 1613, 1823, 1615, 1874, 1616, 1807, 2033))
  [void](MakeProfile $pm 'SHA-CH4-SM' @(1618, 1901, 1619, 1959, 1620, 1922, 1621, 1910, 1622, 1983, 1623, 1831, 1624, 1908, 1626, 1852, 1627, 1891, 1628, 1808, 2032))
  [void](MakeProfile $pm 'SHA-CH5-SM' @(1630, 2018, 1631, 1936, 1632, 1975, 1633, 1829, 1634, 1851, 1635, 1985, 1615))
  [void](MakeProfile $pm 'SHA-CH6-SM' @(1637, 1990, 1638, 1965, 1639, 1838, 1640, 1896, 1641, 1812, 1642, 1818, 2031))
  [void](MakeProfile $pm 'SHA-CH7-SM' @(1644, 1881, 1645, 1945, 1646, 1904, 1648, 1930, 1649, 1867, 1650, 1870, 1651, 1878, 1652, 1880, 1653, 1923, 2030))
  [void](MakeProfile $pm 'SHA-CH8-SS' @(1655, 1976, 1656, 1996, 1657, 1860, 1659, 1864, 1660, 1952, 1786))
  [void](MakeProfile $pm 'SHA-CH9-SS' @(1661, 2009, 1662, 1820, 1663, 1868, 1664, 1854, 1665, 1902, 1666, 1888, 1672))
  $log.WriteLine('profiles after: ' + @($pm.Elements()).Count)
  $m.Save(); $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst)
  $pm = $m.DomainDataSet.ProfileManager; $idsF = $pm.SelectionSetField('SelectionSetElementIDs'); $n = 0
  foreach ($p in $pm.Elements()) { $b = @(); foreach ($i in $idsF.GetValue($p.Id)) { $b += [int]$i }; if ($b.Count -gt 0) { $n++ } }
  $log.WriteLine('after reopen: ' + @($pm.Elements()).Count + ' profiles, ' + $n + ' with elements')
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  Copy-Item $dst, "$dst.sqlite" $share -Force
  foreach ($f in Get-ChildItem $work -Filter 'SewerGEMS Block 04_R1.stsw_*.out') { Copy-Item $f.FullName (Join-Path $share ($f.Name -replace '_R1\.stsw_', '_R2.stsw_')) -Force }
  foreach ($f in Get-ChildItem $work -Filter 'SewerGEMS Block 04_R1.stsw_*.out') { Copy-Item $f.FullName (Join-Path $share $f.Name) -Force }
  Copy-Item "$share\SewerGEMS Block 04.stsw.dwh" "$share\SewerGEMS Block 04_R2.stsw.dwh" -Force
  Copy-Item "$share\SewerGEMS Block 04.stsw.profiles.dwh" "$share\SewerGEMS Block 04_R2.stsw.profiles.dwh" -Force
  $log.WriteLine('delivered R2 (.stsw, .sqlite, .dwh, .profiles.dwh) and the result files of R1 and R2 to the share')
}
$log.ToString()
