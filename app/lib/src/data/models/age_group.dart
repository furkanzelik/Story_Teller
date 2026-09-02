/// Age bands the app generates for. Kept coarse on purpose — the LLM prompt
/// only needs a rough reading level and attention span, and fewer choices means
/// a simpler picker for a tired parent.
enum AgeGroup {
  toddler(id: '2-3', label: '2–3 jaar'),
  preschool(id: '4-5', label: '4–5 jaar'),
  early(id: '6-7', label: '6–7 jaar'),
  older(id: '8-10', label: '8–10 jaar');

  const AgeGroup({required this.id, required this.label});

  final String id;
  final String label;

  static AgeGroup fromId(String id) =>
      AgeGroup.values.firstWhere((g) => g.id == id, orElse: () => preschool);
}
