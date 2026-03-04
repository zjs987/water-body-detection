$(document).ready(function () {
    var t = null;
    t = setTimeout(time, 1000); //開始运行
    function time() {
        clearTimeout(t); //清除定时器
        dt = new Date();
        var y = dt.getFullYear();
        var mt = dt.getMonth() + 1;
        var day = dt.getDate();
        var h = dt.getHours(); //获取时
        var m = dt.getMinutes(); //获取分
        var s = dt.getSeconds(); //获取秒
        var t = null;
        document.getElementById("time").innerHTML = y + "." + Appendzero(mt) + "." + Appendzero(day) + " " + Appendzero(h) + ":" + Appendzero(m) + ":" + Appendzero(s) + "";

        function Appendzero(obj) {
            if (obj < 10) return "0" + "" + obj;
            else return obj;
        }
        t = setTimeout(time, 1000); //设定定时器,循环运行     
    }
})



var txt = 35
option5 = {
    color: 'rgba(255,255,255,.1)',
    series: [{
        name: 'Line 1',
        type: 'pie',
        clockWise: true,
        radius: ['60%', '70%'],
        itemStyle: {
            normal: {
                label: {
                    show: false
                },
                labelLine: {
                    show: false
                }
            }
        },
        hoverAnimation: false,
        data: [{
            value: txt,
            name: '预警比例',
            label: {
                normal: {
                    rich: {
                        a: {
                            color: '#fff',
                            align: 'center',
                            fontSize: 25,
                            fontFamily:"等线",
                            fontWeight: "bold",

                        },
                        b: {
                            color: 'rgba(255,255,255,.5)',
                            align: 'center',
                            padding: -20,
                            fontFamily:"苹方",
                            fontSize: 14
                        }
                    },
                    formatter: function (params) {
                        return "{a|" + params.value + "%}" + "\n\n{b|预警比例}";
                    },
                    position: 'center',
                    show: true,
                    textStyle: {
                        fontSize: '14',
                        fontWeight: 'normal',
                        color: '#fff'
                    }
                }
            },
            itemStyle: {
                normal: {
                    color: { // 完成的圆环的颜色
                        colorStops: [{
                            offset: 0,
                            color: '#00ffde' // 0% 处的颜色
                        }, {
                            offset: 1,
                            color: '#00c5ab' // 100% 处的颜色
                        }]
                    },


                }
            }
        }, {
            name: '未使用',
            value: 100 - txt
        }]
    }]
};

var grids={
    left: '0',
    top: '30',
    right: '20',
    bottom: '0',
    containLabel: true
}

var textStyles={
    color: 'rgba(255,255,255,.5)',
    fontFamily:"苹方"
}

var  legends={
    x: 'center',
    y: '0',
    icon: 'circle',
    itemGap: 8,
    textStyle: {color: 'rgba(255,255,255,.5)'},
    itemWidth: 10,
    itemHeight: 10,
},

option2 = {
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'shadow',
        },   
     

    },
    grid: grids,
    xAxis: {
        type: 'category',
        data: ['lake', 'river', 'wetland', 'ocean', 'pond', 'reservoir', 'other', ],
        axisLine: {show: false},
        axisTick: {show: false},
        axisLabel: {textStyle: textStyles},
    },

    yAxis: {
        type: 'value',
        splitNumber: 4,
        axisLine: {
            show: false
        },
        axisTick: {
            show: false
        },
        splitLine: {
            lineStyle: {
                color: 'rgba(255,255,255,0.05)'
            }
        },
        axisLabel: {
            textStyle:textStyles,
        },
    },
    series: [{
        name: '主要问题分布情况',
        type: 'bar',
        barWidth: '10',
        // label: {
        //     normal: {
        //         show: true,
        //         position: 'top',
        //         textStyle: {
        //             color: "#007a55"
        //         }
        //     }
        // },
        itemStyle: {
            normal: {
                color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [{
                    offset: 0,
                    color: '#00c5ab'
                }, {
                    offset: 1,
                    color: '#01dec1'
                }]),
                barBorderRadius: 11,
            }

        },
        data: [123, 154, 234, 321, 120, 390, 634, 123, 154, 234, 321, 108]

    }]
};


option3 = {
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            lineStyle: {
                color: {
                    type: 'linear',
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [{
                        offset: 0,
                        color: 'rgba(0, 255, 255,0)'
                    }, {
                        offset: 0.5,
                        color: 'rgba(255, 255, 255,0.5)',
                    }, {
                        offset: 1,
                        color: 'rgba(0, 255, 255,0)'
                    }],
                    global: false
                }
            },
        },
        // formatter: '{b}走势',
    },
    legend: {
        x: 'center',
        y: '0',
        icon: 'circle',
        itemGap: 8,
        textStyle: {
            color: 'rgba(255,255,255,.5)'
        },
        itemWidth: 10,
        itemHeight: 10,
    },
    grid: grids,
    xAxis: [{
        type: 'category',
        boundaryGap: false,
        splitLine: {show: false},
        axisTick: {show: false},
        axisLabel: {textStyle: textStyles},
        axisLine: {show: false},
        data: ['1', '2', '3', '4', '5', '6', '7']

    }, {

        axisPointer: {show: false},
        axisLine: {show: false},
        position: 'bottom',
    }],

    yAxis: [{
        type: 'value',
        axisTick: {
            show: false
        },
        splitNumber: 3,
        axisLabel: {
            textStyle: textStyles,
        },
        axisLine: {
            show: false
        },
        splitLine: {
            lineStyle: {
                color: 'rgba(255,255,255,.05)'
            }
        }
    }],
    series: [{

            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 4,
            showSymbol: false,
            lineStyle: {
                normal: {
                    color: '#00ccea',
                    width: 2
                }
            },
            areaStyle: {
                normal: {
                    color: 'rgba(65,196,216,.0)'
                }
            },
            itemStyle: {
                normal: {
                    color: '#00ccea',
                    borderColor: 'rgba(65,196,216,.3)',
                    borderWidth: 7
                }
            },
            data: [60, 20, 50, 10, 70, 40, 130, 40, 180, 60, 80, 40],

        }
    ]
};

option4 = {
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'shadow'
        },
        // formatter: '{b}走势',

    },
    legend: legends,
    grid:grids,
    xAxis: {
        type: 'category',
        data: ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级', '七年级', '八年级', '九年级'],
        axisLine: {
            show: false
        },
        axisTick: {
            show: false
        },
        axisLabel: {
            textStyle:textStyles
        },
    },

    yAxis: {
        type: 'value',
        splitNumber: 2,
        axisLine: {
            show: false
        },
        axisTick: {
            show: false
        },
        splitLine: {
            show: true,
            lineStyle: {
                color: 'rgba(255,255,255,0.05)'
            }
        },
        axisLabel: {
            textStyle:textStyles
        },
    },
    series: [{
            name: '男',
            type: 'bar',
            barWidth: 10,
            itemStyle: {
                normal: {
                    color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [{
                        offset: 0,
                        color: '#00ccea'
                    }, {
                        offset: 1,
                        color: '#49e4fb'
                    }]),
                    barBorderRadius: 11,
                }
            },
            data: [123, 154, 234, 321, 120, 390, 634, 123, 154, 234, 321, 108]

        },
        {
            name: '女',
            type: 'bar',
            barWidth: 10,
            itemStyle: {
                normal: {
                    color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [{
                        offset: 0,
                        color: '#00c5ab'
                    }, {
                        offset: 1,
                        color: '#22ecd2'
                    }]),
                    barBorderRadius: 11,
                }
            },
            data: [63, 194, 234, 321, 278, 110, 534, 63, 194, 234, 321, 278]

        }

    ]
};


option1 = {
    title: {
        left: "center",
        bottom: "20%",
        text: '完成率',
        textStyle: {
            color: 'rgba(255,255,255,.4)',
            fontSize: '14',
            fontWeight:'normal',
            fontFamily:'苹方'
        },
    },
    series: [{
        name: '',
        textStyle: {
            color: '#fff'
        },
        type: 'gauge',
        //仪表盘详情，用于显示数据。
        // 刻度
        radius: "60%",
        splitNumber: 1,
        min: 0,
        max: 100,
        axisLabel: {
            show: false,
        },
        axisLine: { // 坐标轴线
            lineStyle: { // 属性lineStyle控制线条样式
                color: [
                    [0.33, '#00ccea'],
                    [0.66, '#00c5ab'],
                    [1, '#5bd326'],

                ],
                width: 8
            }
        },
        axisTick: { // 坐标轴小标记
            show: true, // 属性show控制显示与否，默认不显示
            splitNumber: 5, // 每份split细分多少段
            length: 13, // 属性length控制线长
            lineStyle: { // 属性lineStyle控制线条样式
                color: 'rgba(255,255,255,.5)',
                width: 1,
                type: 'solid'
            }
        },
        splitLine: { // 分隔线
            length: 0, // 属性length控制线长
            lineStyle: { // 属性lineStyle（详见lineStyle）控制线条样式
                color: 'auto'
            }
        },
        pointer: {
            width: 3 //针宽
        },
        detail: {
            show: true,
            formatter: '{value}%',
            offsetCenter: [0, '35%'],
            textStyle: {
                fontSize: 24,
                fontFamily:"等线",
                color:"#fff"
            }
        },
        data: [{
            value: 80,
        }]
    }]
};


option6 = {
    // legend:legends,
    tooltip: {
        trigger: 'item',
        formatter: "{b} : {c} ({d}%)"
    },
    series: [{
        name: '访问来源',
        type: 'pie',
        radius: ['40%', '65%'],
        //  selectedOffset: 13,
        // selectedMode: 'single',
        center: ['50%', '50%'],
        data: [{
                value: 120,
                name: '男',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [{
                            offset: 1,
                            color: "#00ccea" // 0% 处的颜色
                        },
                        {
                            offset: 0,
                            color: "#53e6fc" // 100% 处的颜色
                        }
                    ], false),
                },
            },
            {
                value: 80,
                name: '女',
                // selected: true,
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [{
                            offset: 1,
                            color: "#00c5ab" // 0% 处的颜色
                        },
                        {
                            offset: 0,
                            color: "#25fade" // 100% 处的颜色
                        }
                    ], false),
                }
            }
        ],
        label: {
            normal: {
                formatter: "{b}：{d}%",
                // position: 'inner',
                textStyle: {
                    color: '#fff'
                }
            },
        },
        labelLine: {
            //show: false
        }

    }]

};

var datazoomstyle1 = [{
    type: 'slider',
    zoomLock: true,
    show: false,
    labelFormatter: () => {
        return '';
    },
    // realtime: true,
    start: 0,
    top: '30%',
    width: 7,
    right: 1,
    bottom: 0,
    // filterMode: 'none',
    end: 100,
    height: '40%',
    // throttle: 0,
    dataBackground: {
        lineStyle: {
            opacity: 0
        },
        areaStyle: {
            opacity: 0
        }
    },
    handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
    handleSize: '0%',
    // handleStyle: {
    //     color: '#3486da',
    //     shadowBlur: 3,
    //     shadowColor: 'rgba(0, 0, 0, 0.6)',
    //     shadowOffsetX: 2,
    //     shadowOffsetY: 2
    // },
    fillerColor: "rgba(52,134,218,0.2)",
    borderColor: "rgba(255,255,255,.07)",
    barBorderRadius: 10,
    yAxisIndex: 0
}, {
    type: "inside",
    yAxisIndex: 0
}]


var labelstyle1 = {
    show: true,
    position: 'right',
    formatter: function (a) {
        return a.value + '%'
    },
    textStyle: {
        color: "rgba(255,255,255,.3)",
        // fontSize: 11,
        // fontFamily:fontFamily

    },
}
var linestyle1 = {
    type: 'dotted',
    color: {
        type: 'linear',
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [{
            offset: 0,
            color: 'rgba(0, 255, 255,0)'
        }, {
            offset: 0.5,
            color: 'rgba(255, 255, 255,0.05)',
        }, {
            offset: 1,
            color: 'rgba(0, 255, 255,0)'
        }],
        global: false
    }
}

option7 = {
    tooltip: {
        trigger: 'axis',
        axisPointer: { // 坐标轴指示器，坐标轴触发有效
            type: 'shadow' // 默认为直线，可选为：'line' | 'shadow'
        }
    },
    legend: legends,
    grid: grids,
    yAxis: {
        type: 'category',
        inverse: true,
        data:['单位名称1', '单位名称2', '单位名称3', '单位名称4', '单位名称5', '单位名称6', '单位名称7', '单位名称8', '单位名称9', '单位名称', '单位名称', '单位名称', '单位名称', '单位名称', '单位名称'],
        axisLine: {
            show: false
        },
        axisTick: {
            show: false
        },

        axisLabel: {
            formatter: function (val) {
                i++
                var strs = val.split(''); //字符串数组
                var str = ''
                for (var i = 0, s; s = strs[i++];) { //遍历字符串数组
                    str += s;
                    if (!(i % 5)) str += '\n'; //按需要求余
                }
                return str

            },
            textStyle: textStyles
        },
    },

    xAxis: {
        type: 'value',
        splitNumber: 4,
        axisLine: {
            lineStyle: {
                color: 'rgba(255,255,255,0.5)'
            }
            // show: false
        },
        axisTick: {
            show: false
        },
        splitLine: {
            show: true,
            lineStyle: linestyle1
        },
        axisLabel: {
            // show: false,
            textStyle: textStyles
        },
    },
    dataZoom: datazoomstyle1,
    series: [{
            name: '一级',
            type: 'bar',
            barWidth: '10%',
            barGap: '100%',
            // label: labelstyle1,
            itemStyle: {
                normal: {
                    color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [{
                        offset: 0,
                        color: '#00ccea'
                    }, {
                        offset: 1,
                        color: '#34e5ff'
                    }]),
                    opacity: '.8',
                    barBorderRadius: 15,
                }
            },
            data: [23, 54, 34, 32, 20, 90, 64, 23, 54, 34, 32, 100, 23, 54, 34, 32]

        },
        {
            name: '二级',
            type: 'bar',
            // label: labelstyle1,
            barWidth: '10%',
            itemStyle: {
                normal: {
                    color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [{
                        offset: 0,
                        color: '#00c5ab'
                    }, {
                        offset: 1,
                        color: '#01dec1'
                    }]),
                    opacity: '.8',
                    barBorderRadius: 15,
                }
            },
            data: [63, 94, 34, 23, 54, 34, 32, 32, 78, 11, 53, 63, 94, 34, 32, 78]

        },
        {
            name: '三级',
            type: 'bar',
            // label: labelstyle1,
            barWidth: '10%',
            itemStyle: {
                normal: {
                    color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [{
                        offset: 0,
                        color: '#3bc000'
                    }, {
                        offset: 1,
                        color: '#6fdf3e'
                    }]),
                    opacity: '.8',
                    barBorderRadius: 15,
                }
            },
            data: [23, 35, 33, 21, 78, 90, 34, 54, 23, 54, 34, 32, 34, 22, 78, 90]
        }
    ]
};
option8 = {
    color: ['#00ccea', '#00c5ab', '#5bd326', '#ffba00'],
    grid: {
        bottom: 0,
        left: 0,
        right: '0'
    },
    //     legend: {
    //     //  orient: 'vertical',
    //     width:'100%',
    //       itemWidth: 10,
    //       itemGap: 5,
    //       itemHeight: 10,
    //       textStyle:{
    //           color:'rgba(255,255,255,.5)'
    //       },
    //         bottom:0,
    //        right:"center",
    //   },
    series: [
        // 主要展示层的
        {
            radius: ['20%', '50%'],
            center: ['50%', '50%'],
            type: 'pie',
            itemStyle: {
                borderRadius: 3,
                borderColor: 'rgba(2,2,2,0)',
                borderWidth: 2
              },
            label: {
                normal: {
                    show: true,
                    formatter: ['{b|{b}:{c}}','{c|{d}%}'].join('\n'),
                    //formatter: ['{b|{b}}','{c|{c}次}', '{d|同比：{d}%}'].join('\n'),
                     rich: {
                   c: {
                       color: 'yellow',
                       fontSize: 16,
                       fontFamily:"等线",
                       fontWeight:'bold',

                   },
                   b: {
                    fontFamily:"苹方",
                       color: 'rgb(98,137,169)',
                       fontSize: 12,
                       height: 20
                   },
               },
               position: 'outside'
                },
                emphasis: {
                    show: true
                }
            },
            labelLine: {
                normal: {
                    show: true,
                //    length: 15,
                //     length2: 30
                },
                emphasis: {
                    show: true
                }
            },
            name: "饼图1",
            data:[
             {"name": "正常","value": 200 }, 
            {"name": "一级关注","value": 200}, 
            {"name": "二级关注","value": 400 },
            {"name": "三级关注","value": 400 } 
        ]

        }
        // , {
        //     name: '外边框',
        //     type: 'pie',
        //     clockWise: false, 
        //     hoverAnimation: false,
        //     radius: ['39.5%', '40%'],
        //     center: ['50%', '40%'],
        //     label: {
        //         normal: {
        //             show: false
        //         }
        //     },
        //     data: [{
        //         value: 9,
        //         name: '',
        //         itemStyle: {
        //             normal: {
        //                 borderWidth: 2,
        //                 borderColor: 'rgba(0,56,185,.1)'
        //             }
        //         }
        //     }]
        // },
    ]
};