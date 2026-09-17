import {describe,it,expect} from "vitest";
import {savingsPreview} from "../src/savings-preview";
describe("explicit what-if dollar assumptions",() => {
  it("prices source hours and allows zero price or zero recovery",() => {
    expect(savingsPreview(100,"2.50","10","25")).toEqual({value:250,low:25,high:62.5});
    expect(savingsPreview(100,"0","0","100")).toEqual({value:0,low:0,high:0});
  });
  it("rejects empty, nonfinite, negative, reversed or out-of-bounds assumptions",() => {
    for (const args of [[100,"","0","25"],[100,"Infinity","0","25"],[100,"-1","0","25"],[100,"2.5","30","25"],[100,"2.5","0","101"],[100,"2.5","-1","25"],[Infinity,"2","0","25"]] as [number,string,string,string][]) expect(savingsPreview(...args)).toBeNull();
  });
});
