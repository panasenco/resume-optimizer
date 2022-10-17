module.exports = {
  // Compare skills first in order of decreasing length and then alphabetically
  skillCompare: (skill0, skill1) => {
    let lengthDiff = skill1.length - skill0.length;
    return lengthDiff == 0 ? skill0.localeCompare(skill1) : lengthDiff;
  },
};
