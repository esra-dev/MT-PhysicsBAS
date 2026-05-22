package tools;

/**
 * Tiny utility class with the primitive / array coercion helpers shared by
 * the CArtAgO artifacts in this package. The agents pass values to operations
 * as {@code Object} or {@code Object[]} (Jason terms may be Number, Boolean,
 * String, …) so every artifact had a near-identical batch of {@code toInt},
 * {@code toDouble}, {@code toIntArray}, … helpers. Centralising them here
 * removes that duplication and keeps the coercion semantics consistent.
 *
 * <p>All methods are static and side-effect free. Null arrays yield empty
 * arrays (defensive default rather than NPE) and null scalars fall back to
 * {@code String.valueOf(null)}-driven parsing so the caller gets a clear
 * {@link NumberFormatException} instead of an opaque NPE.
 */
public final class Converters {

    private Converters() { /* no instances */ }

    // ---- scalars -----------------------------------------------------------

    /** Coerce a Jason term to {@code int}. Accepts Number, Boolean, String. */
    public static int toInt(Object o) {
        if (o instanceof Number)  return ((Number) o).intValue();
        if (o instanceof Boolean) return ((Boolean) o) ? 1 : 0;
        return Integer.parseInt(String.valueOf(o));
    }

    /** Coerce a Jason term to {@code double}. Accepts Number, Boolean, String. */
    public static double toDouble(Object o) {
        if (o instanceof Number)  return ((Number) o).doubleValue();
        if (o instanceof Boolean) return ((Boolean) o) ? 1.0 : 0.0;
        return Double.parseDouble(String.valueOf(o));
    }

    /** Coerce a Jason term to {@code boolean}. Accepts Boolean, Number (0/1), String. */
    public static boolean toBoolean(Object o) {
        if (o instanceof Boolean) return (Boolean) o;
        if (o instanceof Number)  return ((Number) o).intValue() != 0;
        return Boolean.parseBoolean(String.valueOf(o));
    }

    /** Clamp {@code v} to the inclusive range {@code [lo, hi]}. */
    public static int clamp(int v, int lo, int hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    // ---- arrays ------------------------------------------------------------

    /** Convert an Object[] of Jason terms to a primitive {@code int[]}. */
    public static int[] toIntArray(Object[] arr) {
        if (arr == null) return new int[0];
        int[] result = new int[arr.length];
        for (int i = 0; i < arr.length; i++) result[i] = toInt(arr[i]);
        return result;
    }

    /**
     * Convert an Object[] of Jason terms to a primitive {@code double[]}.
     * Malformed elements yield {@link Double#NaN} so callers can still
     * inspect surrounding values rather than aborting on the first bad cell.
     */
    public static double[] toDoubleArray(Object[] arr) {
        if (arr == null) return new double[0];
        double[] result = new double[arr.length];
        for (int i = 0; i < arr.length; i++) {
            Object o = arr[i];
            if (o instanceof Number)  result[i] = ((Number) o).doubleValue();
            else if (o instanceof Boolean) result[i] = ((Boolean) o) ? 1.0 : 0.0;
            else {
                try { result[i] = Double.parseDouble(String.valueOf(o)); }
                catch (NumberFormatException e) { result[i] = Double.NaN; }
            }
        }
        return result;
    }

    /** Convert an Object[] of Jason terms to a {@code String[]} via {@link String#valueOf}. */
    public static String[] toStringArray(Object[] arr) {
        if (arr == null) return new String[0];
        String[] result = new String[arr.length];
        for (int i = 0; i < arr.length; i++) result[i] = String.valueOf(arr[i]);
        return result;
    }

    /** Convert an Object[] of Jason terms to a primitive {@code boolean[]}. */
    public static boolean[] toBooleanArray(Object[] arr) {
        if (arr == null) return new boolean[0];
        boolean[] result = new boolean[arr.length];
        for (int i = 0; i < arr.length; i++) result[i] = toBoolean(arr[i]);
        return result;
    }
}
