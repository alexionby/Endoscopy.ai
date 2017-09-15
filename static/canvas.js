$(function(){

  function Scene(real_canvas, main_canvas) {

    this.main_canvas = main_canvas;
    this.real_canvas = real_canvas;

    this.global_parameters = undefined;

    this.image = undefined;
    this.image_opacity = 100;
    this.image_is_visible = true;

    this.vessels = undefined;
    this.vessels_parameters = undefined;
    this.vessels_opacity = 100;
    this.vessels_is_visible = true;

    this.radius = undefined;
    this.selected_pixel = undefined;

    this.dots = undefined;
    this.dots_opacity = 100;
    this.dots_is_visible = true;

    this.current_vessel = -1;          //state and vessels
    this.selected_vessels = [];
    this.selected_dots = [];

    this.max_width = 0;
    this.max_height = 0;

    this.multiplier = 1;

    this.model = 0;

    this.current_vessel_window = undefined;
    this.vessel_windows = [];

    this.harmonics = undefined;
    this.plot_params = undefined;

    this.states = ['parameters','report'];
    this.current_state = 'parameters';
    this.report_vessels = [];
  }

  Scene.prototype.add_to_report = function() {
    if (this.current_vessel > -1) {
      this.report_vessels.push( this.current_vessel );
    }
  }

  Scene.prototype.set_visible_size = function(container) {

    this.max_width = container.width() * 0.99;
    this.max_height = container.height() * 0.99;

  }

  Scene.prototype.draw_vessels = function() {

    var real_canvas = this.real_canvas;
    var ctx_real = real_canvas.getContext('2d');
    var vessels = this.vessels;

    //ctx_real.save();

    /*
    for (key in vessels) {
      for ( i in vessels[key] ) {

        //ctx_real.globalAlpha = this.vessels_opacity / 100
        ctx_real.beginPath();
        ctx_real.arc(vessels[key][i][1], vessels[key][i][0], 1, 0, 2 * Math.PI, false);
        ctx_real.fillStyle = "rgb(255,0,0)";
        ctx_real.fill();

      }
    }
    //ctx_real.restore()
    */

    var main_canvas = this.main_canvas;
    var ctx_main = main_canvas.getContext('2d');
    var vessels = this.vessels;

    ctx_main.save();
    ctx_main.globalAlpha = this.vessels_opacity / 100

    for ( key in vessels ) {
      for ( i in vessels[key] ) {
        ctx_main.beginPath();
        ctx_main.arc(vessels[key][i][1] * this.multiplier, vessels[key][i][0] * this.multiplier, 1, 0, 2 * Math.PI, false);
        ctx_main.fillStyle = "rgb(255,0,0)";
        ctx_main.fill();
      }
    }

    for ( key of this.report_vessels ) {
      for ( i in vessels[key] ) {
        ctx_main.beginPath();
        ctx_main.arc(vessels[key][i][1] * this.multiplier, vessels[key][i][0] * this.multiplier, 1, 0, 2 * Math.PI, false);
        ctx_main.fillStyle = "rgb(255,0,255)";
        ctx_main.fill();
      }
    }

    if ( this.current_state == 'parameters' ) {
      if (this.current_vessel > -1) {
        for ( i of vessels[this.current_vessel] ) {
          ctx_main.beginPath();
          ctx_main.arc(i[1] * this.multiplier, i[0] * this.multiplier, 1, 0, 2 * Math.PI, false);
          ctx_main.fillStyle = "rgb(0,255,255)";
          ctx_main.fill();
         }
      }
    }

    if ( this.current_state == 'parameters' ) {
      for ( key of this.selected_vessels ) {
        for ( i of vessels[key] ) {
          ctx_main.beginPath();
          ctx_main.arc(i[1] * this.multiplier, i[0] * this.multiplier, 1, 0, 2 * Math.PI, false);
          ctx_main.fillStyle = "rgb(255,255,255)";
          ctx_main.fill();
        }
      }
    }

    if ( this.current_state == 'report' ) {
      for ( key of this.report_vessels) {

        if (vessels[key] === undefined) {
          var index = this.report_vessels.indexOf(key);
          this.report_vessels.splice(index, 1);
        }

        ctx_main.font = "18px Arial";
        ctx_main.fillStyle = "cyan";
        ctx_main.textAlign = "center";
        console.log(vessels[key][0][1], vessels[key].slice(-1)[0][1] )
        console.log( this.multiplier * (vessels[key][0][1] + vessels[key].slice(-1)[0][1]) / 2 )
        ctx_main.fillText(key, this.multiplier * (vessels[key][0][1] + vessels[key].slice(-1)[0][1]) / 2 , this.multiplier * (vessels[key][0][0] + vessels[key].slice(-1)[0][0]) / 2);
      }
    }

    ctx_main.restore()

  }

  //merge is here!!!!
  Scene.prototype.merge_vessels = function() {

    if (this.selected_vessels.length === 2) {

      let index_1 = this.selected_vessels[0];
      let index_2 = this.selected_vessels[1];

      let vess_a = this.vessels[index_1];
      let vess_b = this.vessels[index_2];

      let rad_a = this.radius[index_1];
      let rad_b = this.radius[index_2];

      let params_a = this.vessels_parameters[index_1];
      let params_b = this.vessels_parameters[index_2];

      delete this.vessels[index_1];
      delete this.vessels[index_2];
      delete this.radius[index_1];
      delete this.radius[index_2];
      delete this.harmonics[index_1];
      delete this.harmonics[index_2];
      delete this.plot_params[index_1];
      delete this.plot_params[index_2];
      delete this.vessels_parameters[index_1];
      delete this.vessels_parameters[index_2];

      console.log( vess_a[0],vess_a.slice(-1)[0]);
      console.log( vess_b[0],vess_b.slice(-1)[0]);

      let that = this;

      $.ajax({
        method: "POST",
        url: "/merge",
        data: { vess_a: JSON.stringify(vess_a),
                vess_b: JSON.stringify(vess_b),
                index: Math.min(index_1, index_2),
                rad_a: JSON.stringify(rad_a),
                rad_b: JSON.stringify(rad_b),
                params_a : JSON.stringify(params_a),
                params_b : JSON.stringify(params_b),
              }
      })
        .done(function( response ) {

          index = response['index']

          that.vessels[index] = response['vessel'][index];
          that.vessels_parameters[index] = response['params'][index];
          that.radius[index] = response['radius'][index];

          that.harmonics[index] = response['harmonics'][index];
          that.plot_params[index] = response['plot_params'][index];

          that.selected_vessels = [];
          //that.draw_scene();

          var vessel = index;
          that.current_vessel = vessel;

          $('#param3').text(that.vessels_parameters[vessel][2]);
          $('#param4').text(that.vessels_parameters[vessel][3]);
          $('#param5').text(that.vessels_parameters[vessel][4]);
          $('#param6').text(that.vessels[vessel].length);
          $('#param7').text( +(that.plot_params[vessel]['area_under_curve']).toFixed(4) );
          $('#param8').text( +(that.plot_params[vessel]['bend_count']).toFixed(4) );
          $('#param9').text( +(that.plot_params[vessel]['mean_abs_peaks']).toFixed(4) );
          $('#param10').text( +(that.plot_params[vessel]['std_amplitude']).toFixed(4) );
          $('#param11').text( +(that.plot_params[vessel]['max_amplitude']).toFixed(4) );
          $('#param12').text( +(that.plot_params[vessel]['min_amplitude']).toFixed(4) );

          that.draw_scene();
          that.draw_plot(vessel);

        });

    }

  }

  Scene.prototype.clear_selected_vessels = function() {
    this.selected_vessels = [];
    this.draw_scene();
  }

  Scene.prototype.select_object = function() {

      function getMousePos(canvas, evt) {
        var rect = canvas.getBoundingClientRect();
        return {
          x: evt.clientX - rect.left,
          y: evt.clientY - rect.top
        };
      }

      var vessels = this.vessels;
      var dots = this.dots;
      var canvas = this.main_canvas;
      var that = this;

      $("canvas#main-canvas").contextmenu(function(evt){

        evt.preventDefault();
        evt.stopPropagation();

        var mousePos = getMousePos(canvas, evt);
        var min = 1000;
        var n = 0;
        var m = 0;
        var dot = undefined;

        for (key in dots) {
          var distance = Math.pow(dots[key][1] * that.multiplier - mousePos.x, 2) + Math.pow(dots[key][0] * that.multiplier - mousePos.y , 2);
          if (distance < min) {
            min = distance;
            dot = key;
          }
        }

        if (dot) {

          if (that.selected_dots.includes(dot)) {

            var index = that.selected_dots.indexOf(dot);
            that.selected_dots.splice(index, 1);
            that.draw_scene();

          } else {

            that.selected_dots.push(dot);
            that.draw_scene();
          }

          $('.dots td:last').text(that.selected_dots.length);
        }
      });

      canvas.addEventListener('click', function(evt) {

      console.log(evt)

        var mousePos = getMousePos(canvas, evt);
        var min = 1000;
        var n = 0;
        var m = 0;
        var vessel = undefined;

        for (key in vessels) {
          for ( i in vessels[key] ) {
            var distance = Math.pow(vessels[key][i][1] * that.multiplier - mousePos.x, 2) + Math.pow(vessels[key][i][0] * that.multiplier - mousePos.y , 2);
            if (distance < min) {
              min = distance;
              n = vessels[key][i][1];
              m = vessels[key][i][0];
              vessel = key;
              that.selected_pixel = [n,m,that.radius[key][i]];
            }
          }
        }

        // Adding Object to report_list
        if (evt.ctrlKey) {
          that.selected_vessels.push(vessel);

          if (that.selected_vessels.length > 2) {
            that.selected_vessels.shift();
          }
        }

        $('#param2').text(that.selected_pixel[2]);

        if (that.current_vessel !== vessel) {

          that.current_vessel = vessel

          $('#param3').text(that.vessels_parameters[vessel][2]);
          $('#param4').text(that.vessels_parameters[vessel][3]);
          $('#param5').text(that.vessels_parameters[vessel][4]);
          $('#param6').text(that.vessels[vessel].length);
          $('#param7').text( +(that.plot_params[vessel]['area_under_curve']).toFixed(4) );
          $('#param8').text( +(that.plot_params[vessel]['bend_count']).toFixed(4) );
          $('#param9').text( +(that.plot_params[vessel]['mean_abs_peaks']).toFixed(4) );
          $('#param10').text( +(that.plot_params[vessel]['std_amplitude']).toFixed(4) );
          $('#param11').text( +(that.plot_params[vessel]['max_amplitude']).toFixed(4) );
          $('#param12').text( +(that.plot_params[vessel]['min_amplitude']).toFixed(4) );
          $('#param13').text( +(that.plot_params[vessel]['mean_peaks']).toFixed(4) );
          $('#param14').text( +(that.plot_params[vessel]['std_peaks']).toFixed(4) );
        }

        that.draw_scene();
        that.draw_plot(vessel);

      }, false);
  }

  Scene.prototype.draw_plot = function(index) {

    var trace1 = {
    x: this.harmonics[index][0],
    y: this.harmonics[index][1].map(Math.sqrt),
    mode: 'markers',
    marker: { size: 5 }
    };

    Plotly.newPlot('harmonic-plot', [trace1], layout, {scrollZoom: true, displayModeBar: false});

  }

  Scene.prototype.draw_dots = function() {

    var ctx_main = this.main_canvas.getContext('2d');

    ctx_main.save();
    for (key in this.dots) {

      ctx_main.globalAlpha = this.dots_opacity / 100 * this.dots_is_visible;
      ctx_main.beginPath();
      ctx_main.arc(this.dots[key][1] * this.multiplier, this.dots[key][0] * this.multiplier, 3, 0, 2 * Math.PI, false);
      ctx_main.fillStyle = "rgb(255,255,0)";
      ctx_main.fill();

    }

    for (key of this.selected_dots) {

      ctx_main.globalAlpha = this.dots_opacity / 100 * this.dots_is_visible;
      ctx_main.beginPath();
      ctx_main.arc(this.dots[key][1] * this.multiplier, this.dots[key][0] * this.multiplier, 3, 0, 2 * Math.PI, false);
      ctx_main.fillStyle = "rgb(0,255,255)";
      ctx_main.fill();

    }

    ctx_main.restore();

  }

  Scene.prototype.draw_image = function() {

    var ctx_real = this.real_canvas.getContext('2d');
    ctx_real.drawImage(this.image, 0, 0, this.real_canvas.width, this.real_canvas.height);

    var ctx_main = this.main_canvas.getContext('2d');

    ctx_main.save();
    ctx_main.globalAlpha = this.image_opacity / 100 * this.image_is_visible
    ctx_main.drawImage(this.image, 0, 0, this.main_canvas.width, this.main_canvas.height);
    ctx_main.restore();

  }

  Scene.prototype.draw_scene = function() {

    var ctx_real = this.real_canvas.getContext('2d');

    this.real_canvas.width = this.image.width;
    this.real_canvas.height = this.image.height;

    var ctx_main = this.main_canvas.getContext('2d');

    this.multiplier = Math.min( this.max_width / this.image.width , this.max_height / this.image.height );
    this.main_canvas.width =  this.image.width * this.multiplier;
    this.main_canvas.height = this.image.height * this.multiplier;

    if(typeof this.image !== 'undefined'  && this.image_is_visible !== false) {
      this.draw_image();
    }
    if(typeof this.vessels !== 'undefined' && this.vessels_is_visible !== false) {
      this.draw_vessels();
    }
    if(typeof this.dots !== 'undefined') {
      this.draw_dots();
    }
    if(typeof this.selected_pixel !== 'undefined') {
      this.draw_selected_pixel();
    }

  }

  Scene.prototype.draw_selected_pixel = function() {

    var ctx_main = this.main_canvas.getContext('2d');

    ctx_main.save();
    ctx_main.beginPath();
    ctx_main.arc(this.selected_pixel[0] * this.multiplier, this.selected_pixel[1] * this.multiplier, 2, 0, 2 * Math.PI, false);
    ctx_main.fillStyle = "rgb(0,0,255)";
    ctx_main.fill();
    ctx_main.restore();
  }

  Scene.prototype.set_visibility = function(element) {

    this[element.id.split('-')[0] + '_is_visible'] = !this[element.id.split('-')[0] + '_is_visible'];
    this.draw_scene();
  }


  Scene.prototype.set_opacity = function(element) {

    this[element.id.split('-')[0] + '_opacity'] = element.value;
    this.draw_scene();
  }

  Scene.prototype.open_image = function(element) {

    if ( $("#model").val() === "0") {
      $(".menu-buttons li:nth-child(1)").css("animation","");
      $(".menu-buttons li:nth-child(2)").css({
        "animation": "attention",
        "animation-duration" : "2s",
        "animation-iteration-count" : "infinite"
      });
    }

    var date = + new Date()
    document.cookie = "filename=" + date

    var that = this;
    var fr = new FileReader();
    fr.onload = function(){createImage(that)};
    fr.readAsDataURL($( element )[0].files[0]); //!!!!

    function createImage(scene) {

        scene.image = new Image();
        scene.image.onload = function(){ imageLoaded(scene) };
        scene.image.src = fr.result;
    }

    function imageLoaded(that) {

      that.image_opacity = 100;
      that.image_is_visible = true;

      that.vessels = undefined;
      that.vessels_parameters = undefined;
      that.vessels_opacity = 100;
      that.vessels_is_visible = true;

      that.dots = undefined;
      that.dots_opacity = 100;
      that.dots_is_visible = true;

      that.global_parameters = undefined;

      that.radius = undefined;
      that.selected_pixel = undefined;

      that.current_vessel = -1;
      that.selected_vessels = [];
      that.selected_dots = [];

      that.current_vessel_window = undefined;
      that.vessel_windows = [];

      that.harmonics = undefined;
      that.plot_params = undefined;

      that.report_vessels = [];

      console.log(that);

      $(":checkbox").prop('checked', true);
      $(".menu-layer input[type=range]").val(100);

      that.draw_scene();
      }

    }

  Scene.prototype.segment_image = function() {

    //this.draw_image();

    $('#segment-image').prop('disabled', true);

    $("#segment-image").text("Please, wait");
    $("#segment-image").css({
      "animation": "waiting",
      "animation-duration" : "2s",
      "animation-iteration-count" : "infinite",
    });

    var dataURL = this.real_canvas.toDataURL()
    var blobBin = atob(dataURL.split(',')[1]);
    var array = [];
    for(var i = 0; i < blobBin.length; i++) {
        array.push(blobBin.charCodeAt(i));
    }

    function _arrayBufferToBase64(buffer) {

        var binary = '';
        var bytes = new Uint8Array(buffer);
        var len = bytes.byteLength;
        for (var i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    };

    var file=new Blob([new Uint8Array(array)], {type: 'image/png'});

    var formdata = new FormData();
    formdata.append("img", file);
    formdata.append("model", this.model )
    formdata.append("filename", document.cookie)

    var that = this;

    $.ajax({
       url: "/segm",
       type: "POST",
       data: formdata,
       processData: false,
       contentType: false,
    }).done(function(respond){

      that.image = new Image();
      var image_ready = function() {

        that.draw_scene();
        that.select_object();

      }

      that.vessels = respond['vessels'];
      that.vessels_parameters = respond['parameters'];
      that.radius = respond['radius'];

      that.global_parameters = respond['global_params']
      $('.global .param_value')[0].innerHTML = that.global_parameters['L']
      $('.global .param_value')[1].innerHTML = that.global_parameters['S']
      $('.global .param_value')[2].innerHTML = that.global_parameters['NonZero']
      $('.global .param_value')[3].innerHTML = Math.round(that.global_parameters['lo']*10000)/10000
      $('.global .param_value')[4].innerHTML = Math.round(that.global_parameters['B']*10000)/10000
      $('.global .param_value')[5].innerHTML = Math.round(that.global_parameters['Si']*10000)/10000

      that.harmonics = respond['harmonics'];
      that.plot_params = respond['plot_params'];

      that.dots = respond['dots'];
      $('.dots .param_value')[0].innerHTML = Object.keys(that.dots).length

      that.image.onload = image_ready;
      that.image.src = respond['path'];

      $('#segment-image').prop('disabled', false);
      $("#segment-image").text("Processing");
      $("#segment-image").css("animation","");
    });

  }

  var scene = new Scene( $("#real-canvas")[0], $("#main-canvas")[0] );

  scene.set_visible_size( $('.image') );
  $( window ).resize(function() {

    scene.set_visible_size( $('.image') );
    scene.draw_scene();

  });

  $('#modeTab a#report-tab').click(function (e) {
    e.preventDefault()
    $(this).tab('show')
    scene.current_state = 'report';
    scene.draw_scene();

    $("ul#report-list").empty();

    for (vessel of scene.report_vessels ) {
      $("ul#report-list").append('<li><span>' + vessel + '</span><button type="button" class="btn btn-danger">Del</button></li>');
    }

  });

  $('#modeTab a#parameters-tab').click(function (e) {
    scene.current_state = 'parameters';
  });

  $('#save_report_global_ref').click( function(that=this) {

    var filename, csv, element;
    var columnDelimiter = ';';
    var lineDelimiter = '\n';

    var keys = Object.keys(scene.global_parameters);
    var result = '';

    result += keys.join(columnDelimiter);
    result += lineDelimiter;

    for (key of keys) {
      result += scene.global_parameters[key];
      result += columnDelimiter;
    }

    csv = result.slice(0,-1) + lineDelimiter;

    element = $("#save_report_global_ref");

    filename = element.prev().val() + '.csv' ;

    if (!csv.match(/^data:text\/csv/i)) {
      csv = 'data:text/csv;charset=utf-8,\uFEFF' + encodeURI(csv);
    }

    element.attr({
      "type": "hidden",
      "href": csv,
      "download": filename });
  });

  $('#save_report_csv_ref').click( function(that=this) {

    var data = []
    var temp_link, filename, csv;
    var index_and_params = []

    for ( key of scene.report_vessels ) {

      index_and_params = [key].concat(scene.vessels_parameters[key]);
      index_and_params = index_and_params.concat(scene.harmonics[key][0]);
      index_and_params = index_and_params.concat(scene.harmonics[key][1]);

      data.push(index_and_params.concat(scene.plot_params[key]))

      console.log(scene.plot_params[key])
      console.log(scene.harmonics[key])
    }

    columnDelimiter = ';';
    lineDelimiter = '\n';

    header = ['Номер','Мин. радиус', 'Макс. радиус', 'Ср. радиус','СКО радиуса','Площадь']
      .concat(["x0","x1","x2","x3","x4","x5","x6","x7","x8","x9"])
      .concat([0,1,2,3,4,5,6,7,8,9])
      .concat(['Площадь под кривой','Количество перегибов','Макс. амплитуда',
               'Средняя амплитуда пиков', 'Средняя амплитуда', 'Мин. амплитуда', 'Дисперсия амплитуды', 'Дисперсия пиков']);

    keys = []
    keys = keys.concat(Object.keys(index_and_params)); //.concat( Object.keys(scene.plot_params) ) ;
    keys = keys.concat(Object.keys(scene.plot_params[0]));

    console.log(keys)
    console.log(data)

    result = '';
    result += header.join(columnDelimiter);
    result += lineDelimiter;

    data.forEach(function(item) {
        console.log(item)

        ctr = 0;
        keys.forEach(function( key ) {

            console.log(key);
            console.log(item[key]);

            if (ctr > 0) result += columnDelimiter;

            result += item[key] || item[ item.length - 1 ][key];
            ctr++;
        });
        result += lineDelimiter;
    });

    filename = $("#save_report_csv_ref").prev().val() + '.csv' ;

    csv = result;

    if (!csv.match(/^data:text\/csv/i)) {
      if (navigator.platform.slice(0,3) === "Win") {
        csv = 'data:text/csv;charset=utf-8,' + csv;
      } else {
        csv = 'data:text/csv;charset=windows-1252,' + csv;
      };
    }

    temp_link = $("#save_report_csv_ref")[0]; //document.createElement('a');
    temp_link.setAttribute("type", "hidden"); // make it hidden if needed
    temp_link.setAttribute('href', data);
    temp_link.setAttribute('download', filename);
  });

  $('#save_report_img_ref').click( function(that=this) {
    var dataURL = $("#main-canvas")[0].toDataURL('image/png');
    this.href = dataURL;
    this.download = $('#save_report_img_ref').prev().val();
  });

  $('#modeTab a#parameters-tab').click(function (e) {
    e.preventDefault()
    $(this).tab('show')
    scene.draw_scene();
  });

  $('#report-list').on('click','button', function() {

    var index = scene.report_vessels.indexOf( $(this).prev().text() );

    console.log(index)

    scene.report_vessels.splice( index, 1 );

    console.log(scene.report_vessels);

    $(this).parent().remove();
    scene.draw_scene();
  });

  $("#erase-dots-btn").click( function(){
    scene.selected_dots = [];
    scene.draw_scene();
  });

  $("#del-dots-btn").click( function(){

    for ( key of scene.selected_dots ) {
      delete scene.dots[key];
    }

    $('.dots td.param_value').text(Object.keys(scene.dots).length);
    $('.dots td:last').text(0);

    $('.dots td:last').text(0);

    scene.global_parameters['B'] = math.divide( Object.keys(scene.dots).length , scene.global_parameters['L'])
    $('.global .param_value')[4].innerHTML = math.round( scene.global_parameters['B'], 4)

    scene.global_parameters['Si'] = math.divide( scene.global_parameters['lo'] , scene.global_parameters['B'])
    $('.global .param_value')[5].innerHTML = math.round( scene.global_parameters['Si'], 4)

    scene.selected_dots = [];
    scene.draw_scene();

  });

  $("#model").change( function(){

    this.model = $("#model").val();

    if (this.model === "0"){
      $('#segment-image').prop('disabled', true);

      $(".menu-buttons li:nth-child(2)").css({
        "animation": "attention",
        "animation-duration" : "2s",
        "animation-iteration-count" : "infinite"
      });

    } else {
      $('#segment-image').prop('disabled', false);
      $(".menu-buttons li:nth-child(2)").css("animation","");
      $(".menu-buttons li:nth-child(3) * ").css({
        "animation": "attention",
        "animation-duration" : "2s",
        "animation-iteration-count" : "infinite"
      });
    }
  });

  $("#open-image").change( function(){ scene.open_image(this); });
  $(":checkbox").change( function(){ scene.set_visibility(this); } );
  $("input[type=range]").change( function(){ scene.set_opacity(this); } );
  $("#segment-image").click( function(){ scene.segment_image(); });
  $("select#model").change( function(){ scene.model = this.value; });
  $("#merge_btn").click(function(){ scene.merge_vessels(); });
  $("#clear_list_btn").click(function(){ scene.clear_selected_vessels(); });
  $("#add_to_report_btn").click(function(){ scene.add_to_report(this); });
  $("#save-image-btn").click( function(){
    var dataURL = $("#main-canvas")[0].toDataURL('image/png');
    this.href = dataURL;
  });

  scene.model = "0";
  $('#model').val("0");
  $("#segment-image").prop('disabled',true);

  $(".menu-buttons li:nth-child(1)").css({
    "animation": "attention",
    "animation-duration" : "2s",
    "animation-iteration-count" : "infinite"
  });

// ввести переменную "состояние""

});
