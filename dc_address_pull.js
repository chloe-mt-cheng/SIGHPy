function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function pully(){
  var big_array = [];
  var element_array = document.getElementsByTagName("tr");
  var element_array_length = element_array.length;
  var start_index = 1;
  do {
    // console.log(element_array_length);
    for (i=start_index;i<element_array_length;i++) {
      console.log(i)
      element_array[i].click();
      await sleep(200);
      var sidebar = document.getElementsByClassName("section contact")[0];
      var sidebar_address = sidebar.innerText.split("\n").slice(0,3);
      big_array.push(sidebar_address);
      // console.log(sidebar_address);
      // await sleep(300);
    };
    var next_button = document.getElementsByClassName("button transparent more")[0];
    next_button.click();
    start_index = element_array_length;
    element_array = document.getElementsByTagName("tr");
    element_array_length = element_array.length;
  }
  while(element_array_length-start_index == 500);
  let csvContent = "data:text/csv;charset=utf-8,";
  big_array.forEach(function(rowArray) {
    let row = rowArray.join(",");
    csvContent += row + "\r\n";
  });
  var encodedUri = encodeURI(csvContent);
  console.log(encodedUri);
  return encodedUri;
};
